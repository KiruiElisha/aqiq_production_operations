// Copyright (c) 2024, RONOH and contributors
// For license information, please see license.txt

let workstationPromptShown = false;

frappe.ui.form.on('Job Card Tool', {
    refresh: function(frm) {
        addCustomCSS();
        loadFiltersFromServer(frm);
        addWorkstationFilterButton(frm);

        // Remove the setInterval and use a more efficient refresh mechanism
        setupRefreshMechanism(frm);

        addFilterButtons(frm);
        frm.disable_save();
    },
    onload: function(frm) {
        initializeJobCardStatus(frm);
    },
    on_unload: function(frm) {
        // Clear any existing intervals or event listeners
        if (frm.auto_refresh_interval) {
            clearInterval(frm.auto_refresh_interval);
        }
        frappe.realtime.off('job_card_update');
    }
});

function setupRefreshMechanism(frm) {
    // Clear any existing interval
    if (frm.auto_refresh_interval) {
        clearInterval(frm.auto_refresh_interval);
    }

    // Set up real-time updates
    frappe.realtime.off('job_card_update');
    frappe.realtime.on('job_card_update', function() {
        silentlyUpdateJobCards(frm);
    });

    // Initial refresh
    refreshJobCards(frm);

    // Set up a less frequent background refresh
    frm.auto_refresh_interval = setInterval(() => {
        if (!document.hidden) {
            silentlyUpdateJobCards(frm);
        }
    }, 60000); // Silently update every minute when the tab is visible
}

async function silentlyUpdateJobCards(frm) {
    try {
        const response = await frm.call({
            method: 'get_job_cards',
            args: {
                status: frm.doc.job_card_status || ['Open', 'Work In Progress', 'On Hold', 'Completed', 'Cancelled', 'Material Transferred'],
                workstations: frm.doc.filtered_workstations.split(',')
            },
            freeze: false
        });

        if (response.message) {
            const $wrapper = $(frm.fields_dict['workstation_dashboard'].wrapper);
            const jobCards = response.message;
            const groupedJobCards = groupJobCardsByStatus(jobCards);
            
            await updateJobCardGroups($wrapper, groupedJobCards);
            
            removeNonExistentJobCards($wrapper, jobCards);
            updateGroupCounts($wrapper);
            
            bindActionEvents(frm);
            bindLinkEvents();
        }
    } catch (error) {
        console.error("Error updating job cards:", error);
        frappe.msgprint(__("An error occurred while updating job cards. Please refresh the page."));
    }
}

function groupJobCardsByStatus(jobCards) {
    return jobCards.reduce((acc, jobCard) => {
        if (jobCard.status && typeof jobCard.status === 'string') {
            if (!acc[jobCard.status]) {
                acc[jobCard.status] = [];
            }
            acc[jobCard.status].push(jobCard);
        } else {
            console.warn(`Job card ${jobCard.name} has an invalid status:`, jobCard.status);
        }
        return acc;
    }, {});
}

async function updateJobCardGroups($wrapper, groupedJobCards) {
    const statusOrder = ['Work In Progress', 'Open', 'Material Transferred', 'On Hold', 'Completed', 'Cancelled'];
    
    for (const status of statusOrder) {
        let $group = $wrapper.find(`.job-cards-group[data-status="${status}"]`);
        
        if (groupedJobCards[status] && groupedJobCards[status].length > 0) {
            const jobCardTiles = await Promise.all(groupedJobCards[status].map(renderJobCardTile));
            
            if ($group.length === 0) {
                $group = $(`
                    <div class="job-cards-group" data-status="${status}">
                        <h3>${status}</h3>
                        <div class="job-cards-grid"></div>
                    </div>
                `);
                $wrapper.append($group);
            }
            
            const $grid = $group.find('.job-cards-grid');
            $grid.empty().append(jobCardTiles);
        } else if ($group.length > 0) {
            $group.remove();
        }
    }

    // Remove any groups that are not in the statusOrder
    $wrapper.find('.job-cards-group').each(function() {
        const groupStatus = $(this).data('status');
        if (!statusOrder.includes(groupStatus)) {
            $(this).remove();
        }
    });
}

function removeNonExistentJobCards($wrapper, jobCards) {
    const currentJobCardNames = jobCards.map(jc => jc.name);
    $wrapper.find('.job-card-tile').each(function() {
        const jobCardName = $(this).data('job-card');
        if (!currentJobCardNames.includes(jobCardName)) {
            $(this).remove();
        }
    });
}

function updateGroupCounts($wrapper) {
    $wrapper.find('.job-cards-group').each(function() {
        const $group = $(this);
        const status = $group.data('status');
        const count = $group.find('.job-card-tile').length;
        $group.find('h3').text(`${status} (${count})`);
        if (count === 0) {
            $group.remove();
        }
    });
}


function checkLoginStatus(frm) {
    const isLoggedIn = localStorage.getItem('logged_in_workstation') !== null;
    if (isLoggedIn) {
        loadFiltersFromServer(frm);
    } else {
        frm.doc.filtered_workstations = '';
        frm.refresh_field('filtered_workstations');
        $(frm.fields_dict['workstation_dashboard'].wrapper).empty();
        frm.page.clear_actions_menu();
    }
}

function loadFiltersFromServer(frm) {
    frappe.call({
        method: "aqiq_production_operations.aqiq_production_operations.rest.job_card_filters.get_user_filters",
        callback: function(r) {
            if (r.message && r.message.filtered_workstations) {
                console.log("Filters received from server:", r.message);
                applyFilterSettings(frm, r.message);
            } else {
                const localFilters = JSON.parse(localStorage.getItem('job_card_filters') || '{}');
                if (localFilters.filtered_workstations) {
                    console.log("Filters from local storage:", localFilters);
                    applyFilterSettings(frm, localFilters);
                    saveFiltersToServer(frm);
                } else {
                    console.log("Prompting for workstation configuration...");
                    promptForWorkstationConfiguration(frm);
                }
            }
        },
        error: function(err) {
            console.error("Error loading filters:", err);
        }
    });
}

function applyFilterSettings(frm, filters) {
    frm.doc.job_card_status = filters.job_card_status || ['Open', 'Work In Progress', 'On Hold', 'Material Transferred'];
    frm.doc.filtered_workstations = filters.filtered_workstations || '';
    frm.refresh_field('job_card_status');
    frm.refresh_field('filtered_workstations');
    localStorage.setItem('job_card_filters', JSON.stringify(filters));
    refreshJobCards(frm);
}

function saveFiltersToServer(frm) {
    const filters = {
        job_card_status: frm.doc.job_card_status,
        filtered_workstations: frm.doc.filtered_workstations
    };
    
    frappe.call({
        method: "aqiq_production_operations.aqiq_production_operations.rest.job_card_filters.save_user_filters",
        args: {
            filters: JSON.stringify(filters) // Convert to JSON string
        },
        callback: function(r) {
            if (r.message && r.message.success) {
                localStorage.setItem('job_card_filters', JSON.stringify(filters));
                frappe.show_alert({
                    message: __('Filters saved successfully'),
                    indicator: 'green'
                });
                refreshJobCards(frm);
            } else {
                frappe.show_alert({
                    message: __('Failed to save filters'),
                    indicator: 'red'
                });
            }
        },
        error: function(err) {
            console.error("Error saving filters:", err);
        }
    });
}

function promptForWorkstationConfiguration(frm) {
    let scanTimeout;
    const SCAN_DELAY = 100; // Reduced from 500ms to 100ms for faster response

    const d = new frappe.ui.Dialog({
        title: __('Configure Workstation'),
        fields: [
            {
                label: __('Scan Data'),
                fieldname: 'scanned_data',
                fieldtype: 'Data',
                options: 'Barcode',
                description: __('Scan QR Code or Barcode'),
                reqd: 1,
                onchange: () => {
                    clearTimeout(scanTimeout);
                    scanTimeout = setTimeout(() => {
                        const scannedData = d.get_value('scanned_data');
                        if (scannedData) {
                            handleScannedData(frm, d, scannedData);
                        }
                    }, SCAN_DELAY);
                }
            },           
            {
                label: __('Workstation'),
                fieldname: 'workstation',
                fieldtype: 'Data',
                read_only: 1
            },
            {
                label: __('Password'),
                fieldname: 'password',
                fieldtype: 'Password',
                reqd: 0,
                hidden: 1
            }
        ],
        primary_action_label: __('Apply'),
        primary_action(values) {
            applyWorkstationConfiguration(frm, values.workstation);
            d.hide();
            showSuccessMessage();
        }
    });

    d.show();

    // Add QR code scanner icon after dialog is shown
    setTimeout(() => {
        const $input = d.fields_dict.scanned_data.$input;
        $input.attr('autocomplete', 'off'); // Disable browser autocomplete
        $input.attr('spellcheck', 'false'); // Disable spellcheck
        $input.attr('autocorrect', 'off'); // Disable autocorrect
        $input.attr('autocapitalize', 'off'); // Disable autocapitalize
        $input.css('padding-right', '30px'); // Make space for the icon
        $input.after('<span class="qr-scanner-icon"><i class="fa fa-qrcode"></i></span>');
        
        // Style the QR scanner icon
        const $icon = $input.next('.qr-scanner-icon');
        $icon.css({
            position: 'absolute',
            right: '10px',
            top: '50%',
            transform: 'translateY(-50%)',
            cursor: 'pointer',
            color: 'var(--text-muted)'
        });

        // Bind click event to QR scan icon
        $icon.on('click', () => {
            frappe.require('qrcode.min.js', () => {
                const scanner = new frappe.ui.Scanner({
                    dialog: true,
                    multiple: false,
                    on_scan(data) {
                        handleScannedData(frm, d, data);
                    }
                });
                scanner.show();
            });
        });

        // Prevent form submission on Enter key press
        $input.on('keydown', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                const scannedData = $(this).val().trim();
                if (scannedData) {
                    handleScannedData(frm, d, scannedData);
                }
            }
        });

        $input.focus();
    }, 0);
}

function handleScannedData(frm, dialog, scanned_data) {
    try {
        console.log("Raw scanned data:", scanned_data);
        console.log("Type of scanned data:", typeof scanned_data);
        
        let decodedData;
        if (typeof scanned_data === 'object' && scanned_data.hasOwnProperty('decodedText')) {
            // If scanned_data is an object with a 'decodedText' property, use that
            decodedData = decodeScannedData(scanned_data.decodedText);
        } else if (typeof scanned_data === 'string') {
            // If scanned_data is already a string, use it directly
            decodedData = decodeScannedData(scanned_data);
        } else {
            throw new Error("Unexpected scanned data format");
        }
        
        dialog.set_value('workstation', decodedData.workstation);
        dialog.set_value('password', decodedData.password);
        
        // Clear the scanned data field
        dialog.set_value('scanned_data', '');
        
        // Immediately apply the configuration
        applyWorkstationConfiguration(frm, decodedData.workstation);
        dialog.hide();
        showSuccessMessage();
    } catch (error) {
        console.error("Scanning error:", error);
        frappe.show_alert({
            message: __("Invalid scanned data: ") + error.message,
            indicator: 'red'
        });
        dialog.set_value('scanned_data', '');
        dialog.fields_dict.scanned_data.input.focus();
    }
}

function decodeScannedData(scannedData) {
    console.log("Attempting to decode:", scannedData);

    let decoded;

    try {
        if (typeof scannedData !== 'string') {
            throw new Error("Scanned data is not a string");
        }

        // Decode the base64 string
        const jsonString = atob(scannedData);
        console.log("Base64 decoded string:", jsonString);
        
        // Parse the JSON string
        decoded = JSON.parse(jsonString);
        console.log("Successfully parsed JSON:", decoded);
    } catch (error) {
        console.error("Decoding error:", error);
        throw new Error("Failed to decode scanned data: " + error.message);
    }

    // Validate the decoded data structure
    if (!decoded || typeof decoded !== 'object') {
        throw new Error("Invalid QR code: Decoded data is not an object");
    }
    if (!decoded.workstation) {
        throw new Error("Invalid QR code: Missing workstation");
    }
    if (!decoded.password) {
        throw new Error("Invalid QR code: Missing password");
    }

    console.log("Successfully decoded data:", decoded);
    return decoded;
}
function showSuccessMessage() {
    frappe.show_alert({
        message: __('Workstation configuration applied successfully'),
        indicator: 'green'
    });
}

function applyWorkstationConfiguration(frm, workstation) {
    frm.doc.filtered_workstations = workstation;
    saveFiltersToServer(frm);
    localStorage.setItem('logged_in_workstation', workstation); // Set login state
    frm.refresh_field('filtered_workstations');
    addWorkstationFilterButton(frm);
}


function initializeJobCardStatus(frm) {
    frm.doc.job_card_status = frm.doc.job_card_status || ['Open', 'Work In Progress', 'On Hold', 'Material Transferred'];
}

function addFilterButtons(frm) {
    addStatusFilterButton(frm);
    addWorkstationFilterButton(frm);
}

function addStatusFilterButton(frm) {
    const statuses = ['Open', 'Work In Progress', 'On Hold', 'Completed', 'Cancelled', 'Material Transferred'];

    frm.page.add_inner_button(__('Filter Status'), function() {
        new frappe.ui.Dialog({
            title: __('Filter Job Cards by Status'),
            fields: statuses.map(status => ({
                label: __(status),
                fieldname: status.toLowerCase().replace(/\s+/g, '_'),
                fieldtype: 'Check',
                default: frm.doc.job_card_status.includes(status)
            })),
            primary_action_label: __('Apply'),
            primary_action(values) {
                frm.doc.job_card_status = Object.entries(values)
                    .filter(([_, value]) => value)
                    .map(([key, _]) => key.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' '));

                saveFiltersToServer(frm);
                refreshJobCards(frm);
                this.hide();
            }
        }).show();
    });
}

function addWorkstationFilterButton(frm) {
    console.log("Adding workstation filter button");

    // Remove previous buttons to avoid duplicates
    frm.page.remove_inner_button('Filter Workstations');
    frm.page.remove_inner_button('Login');
    frm.page.remove_inner_button('Logout');

    const isLoggedIn = localStorage.getItem('logged_in_workstation') !== null;
    console.log("Is Logged In:", isLoggedIn);

    if (!isLoggedIn) {
        frm.page.add_inner_button(__('Login'), function() {
            promptForWorkstationConfiguration(frm);
        });
    } else {
        frm.page.add_inner_button(__('Logout'), function() {
            frappe.confirm(
                __('Are you sure you want to logout from the current workstation?'),
                async function() {
                    try {
                        await frappe.call({
                            method: "aqiq_production_operations.aqiq_production_operations.rest.job_card_filters.clear_user_filters",
                            callback: function(r) {
                                if (r.message && r.message.success) {
                                    localStorage.removeItem('job_card_filters');
                                    localStorage.removeItem('logged_in_workstation'); // Remove login state
                                    frm.doc.filtered_workstations = '';
                                    frm.refresh_field('filtered_workstations');

                                    frappe.show_alert({
                                        message: __('Logged out successfully'),
                                        indicator: 'green'
                                    });

                                    window.location.reload();
                                }
                            },
                            error: function(err) {
                                console.error("Error during logout:", err);
                            }
                        });
                    } catch (error) {
                        frappe.msgprint(__('Failed to logout. Please try again.'));
                    }
                }
            );
        });
    }
}

function getCustomerName(workOrder) {
    return new Promise((resolve) => {
        frappe.db.get_value('Work Order', workOrder, 'custom_customer_name', (r) => {
            resolve(r.custom_customer_name || ' ');
        });
    });
}

let previousJobCardsData = {};

function refreshJobCards(frm) {
    if (frm.doc.__islocal || !frm.doc.filtered_workstations) return;

    const lastScrollPosition = window.pageYOffset;

    frm.call({
        method: 'get_job_cards',
        args: {
            status: frm.doc.job_card_status || ['Open', 'Work In Progress', 'On Hold', 'Completed', 'Cancelled', 'Material Transferred'],
            workstations: frm.doc.filtered_workstations.split(',')
        },
        freeze: false,
        callback: function(r) {
            if (r.message) {
                renderJobCards(frm, r.message);
                addJobCardActions(frm, r.message);
                frm.page.set_indicator('Updated', 'green');
                updateFilterIndicator(frm);
                
                
                // Restore scroll position after rendering
                setTimeout(() => window.scrollTo(0, lastScrollPosition), 0);
            }
        }
    });
}
async function renderJobCards(frm, jobCards) {
    const $wrapper = $(frm.fields_dict['workstation_dashboard'].wrapper);
    $wrapper.empty();

    const groupedJobCards = groupJobCardsByStatus(jobCards);

    const statusOrder = ['Work In Progress', 'Open', 'Material Transferred', 'On Hold', 'Completed', 'Cancelled'];

    const htmlPromises = statusOrder.map(async (status) => {
        if (!groupedJobCards[status] || groupedJobCards[status].length === 0) return '';

        const jobCardTiles = await Promise.all(groupedJobCards[status].map(renderJobCardTile));

        return `
            <div class="job-cards-group">
                <h3>${status} (${groupedJobCards[status].length})</h3>
                <div class="job-cards-grid">
                    ${jobCardTiles.join('')}
                </div>
            </div>
        `;
    });

    const html = (await Promise.all(htmlPromises)).join('');

    $wrapper.html(html);
    bindActionEvents(frm);
    bindLinkEvents();
}


async function renderJobCardTile(jobCard) {
    const customerName = await getCustomerName(jobCard.work_order);
    const itemNameResult = await frappe.db.get_value('Job Card', jobCard.name, 'production_item');
    const itemName = itemNameResult.message.production_item || 'N/A';
    
    // Fetch Material Request details
    const mrDetails = await getMaterialRequestDetails(jobCard.name);

    let mrInfo = '';
    if (jobCard.status === 'Material Transferred') {
        mrInfo = `<p><strong>Materials:</strong> <span style="color: green;">Transferred</span></p>`;
    } else if (mrDetails.hasMaterialRequest) {
        mrInfo = `<p><strong>Materials:</strong> ${mrDetails.hasReceivedQty ? '<span style="color: green;">Transferred</span>' : '<span style="color: red;">Not transferred</span>'}</p>`;
    }

    return `
       <div class="job-card-tile ${jobCard.custom_is_active === "1" ? 'active-job-card' : ''}" data-job-card="${jobCard.name}">
            <div class="job-card-header" style="background-color: ${getStatusColor(jobCard.status)};">
                <div class="job-card-name">
                    <a href="#" class="job-card-link" data-route="Form/Job Card/${encodeURIComponent(jobCard.name)}">${jobCard.name}</a>
                </div>
                <div class="job-card-status">
                    ${jobCard.status}
                </div>
            </div>
            <div class="job-card-body">
                <p><strong>Customer:</strong> <span style="font-size: 1.2em; font-weight: bold;">${customerName}</span></p>
                <p><strong>Item:</strong> 
                    <a href="/app/item/${encodeURIComponent(itemName)}" class="item-link">${itemName}</a>
                </p>
                <p><strong>Operation:</strong> ${jobCard.operation}</p>
                <p><strong>Workstation:</strong> ${jobCard.workstation}</p>
                <p><strong>Started At:</strong> ${formatDateTime(jobCard.actual_start_date)}</p>
                <p><strong>Work Order:</strong> 
                    <a href="#" class="work-order-link" data-route="Form/Work Order/${encodeURIComponent(jobCard.work_order)}">${jobCard.work_order}</a>
                </p>
                <p><strong>Qty:</strong> ${jobCard.total_completed_qty} / ${jobCard.for_quantity}</p>
                <p><strong>Active:</strong> ${jobCard.custom_is_active === "1" ? 'Yes' : 'No'}</p>
                ${mrInfo}
            </div>
            <div class="job-card-actions">
                ${getActionButtons(jobCard)}
            </div>
        </div>
    `;
}

async function getMaterialRequestDetails(jobCardName) {
    try {
        const jobCardDetails = await frappe.db.get_value('Job Card', jobCardName, 'status');
        if (jobCardDetails.message.status === 'Material Transferred') {
            return { hasMaterialRequest: true, hasReceivedQty: true };
        }

        const result = await frappe.db.get_list('Material Request', {
            filters: { 'job_card': jobCardName },
            fields: ['name']
        });

        if (result.length === 0) {
            return { hasMaterialRequest: false };
        }

        const mrItems = await frappe.db.get_list('Material Request Item', {
            filters: { 'parent': result[0].name },
            fields: ['received_qty']
        });

        const hasReceivedQty = mrItems.some(item => item.received_qty > 0);

        return { hasMaterialRequest: true, hasReceivedQty: hasReceivedQty };
    } catch (error) {
        console.error("Error fetching Material Request details:", error);
        return { hasMaterialRequest: false };
    }
}

function getEmployeeDisplay(jobCard) {
    return jobCard.employee && jobCard.employee.length > 0 ? jobCard.employee.map(emp => emp.employee).join(', ') : 'Not Assigned';
}

function bindLinkEvents() {
    $('.job-card-link, .work-order-link').on('click', function(e) {
        e.preventDefault();
        frappe.set_route($(this).data('route'));
    });
}

function bindActionEvents(frm) {
    $('.btn-start').on('click', function() {
        startJob(frm, $(this).data('job-card'));
    });

    $('.btn-pause').on('click', function() {
        pauseJob(frm, $(this).data('job-card'));
    });

    $('.btn-complete').on('click', function() {
        completeJob(frm, $(this).data('job-card'));
    });

    $('.btn-submit').on('click', function() {
        submitJob(frm, $(this).data('job-card'));
    });

    $('.btn-resume').on('click', function() {
        resumeJob(frm, $(this).data('job-card'));
    });
}

async function completeJob(frm, jobCard) {
    try {
        // Load the Job Card document
        await frappe.model.with_doc('Job Card', jobCard);
        let doc = frappe.get_doc('Job Card', jobCard);
        let qtyToManufacture = doc.for_quantity;
        let completedQty = doc.total_completed_qty || 0;
        let remainingQty = qtyToManufacture - completedQty;

        if (remainingQty <= 0) {
            frappe.msgprint(__('No quantity left to complete.'));
            return;
        }

        // Fetch the employee assigned to the job card
        const employeeResponse = await frappe.call({
            method: "aqiq_production_operations.aqiq_production_operations.rest.update_jobcard.get_job_card_employees",
            args: { job_card_id: jobCard }
        });

        if (!employeeResponse.message.success || employeeResponse.message.employees.length === 0) {
            frappe.msgprint(__('No employees found for this job card.'));
            return;
        }

        const employee = employeeResponse.message.employees[0]; // Assuming the first employee in the list

        // Prompt user for completed quantity
        let fields = [
            {
                fieldname: 'completed_qty',
                label: __('Completed Quantity'),
                fieldtype: 'Float',
                reqd: 1,
                default: remainingQty,
                description: `Quantity to manufacture: ${qtyToManufacture}, Already completed: ${completedQty}, Remaining: ${remainingQty}`
            }
        ];

        frappe.prompt(fields, async function(values) {
            let newCompletedQty = values.completed_qty;

            if (newCompletedQty <= 0 || newCompletedQty > remainingQty) {
                frappe.msgprint(__('Invalid completed quantity.'));
                return;
            }

            try {
                // Calculate the new total completed quantity
                let newTotalCompletedQty = completedQty + newCompletedQty;

                // Call the existing `make_time_log` method
                await frappe.call({
                    method: "erpnext.manufacturing.doctype.job_card.job_card.make_time_log",
                    args: {
                        args: JSON.stringify({
                            job_card_id: jobCard,
                            completed_qty: newCompletedQty,
                            complete_time: frappe.datetime.now_datetime()
                        })
                    }
                });

                // Update the Job Card document with new completed quantity
                await frappe.call({
                    method: "frappe.client.set_value",
                    args: {
                        doctype: "Job Card",
                        name: jobCard,
                        fieldname: {
                            "total_completed_qty": newTotalCompletedQty
                        }
                    }
                });

                // Check if the job is completed
                if (newTotalCompletedQty >= qtyToManufacture) {
                    await updateJobCardStatus(frm, jobCard, "Completed", false);
                    frappe.show_alert(__('Job completed successfully.'));
                } else {
                    await updateJobCardStatus(frm, jobCard, "Work In Progress", false);
                }

                refreshJobCards(frm);
            } catch (error) {
                frappe.msgprint(__('Failed to update the job card time log. Please try again.'));
                console.error(error);
            }
        }, __('Enter Completed Quantity'), __('Complete Job'));
    } catch (error) {
        frappe.msgprint(__('Failed to load the job card. Please try again.'));
        console.error(error);
    }
}

function getActionButtons(jobCard) {
    let buttons = '';
    const remainingQty = jobCard.for_quantity - (jobCard.total_completed_qty || 0);
    const hasStarted = jobCard.status === 'Work In Progress' || jobCard.status === 'On Hold';
    const isNotActive = jobCard.custom_is_active == 0;

    if (jobCard.total_completed_qty < jobCard.for_quantity) {
        if (jobCard.custom_is_active == 1) {
            buttons += `
                <button class="btn btn-warning btn-xs btn-pause" data-job-card="${jobCard.name}">Pause</button>
                <button class="btn btn-success btn-xs btn-complete" data-job-card="${jobCard.name}">Complete</button>
            `;
        } else {
            if (jobCard.status === 'Open' || jobCard.status === 'Material Transferred' || (jobCard.status === 'Work In Progress' && remainingQty > 0)) {
                buttons += `<button class="btn btn-primary btn-xs btn-start" data-job-card="${jobCard.name}">Start</button>`;
            }
            if (jobCard.status === 'On Hold' && remainingQty > 0) {
                buttons += `<button class="btn btn-info btn-xs btn-resume" data-job-card="${jobCard.name}">Resume</button>`;
            }
        }
    }

    if (hasStarted && (jobCard.custom_is_active == 0 || jobCard.total_completed_qty > 0)) {
        buttons += `<button class="btn btn-info btn-xs btn-submit" data-job-card="${jobCard.name}">Submit</button>`;
    }

    return buttons;
}


async function submitJob(frm, jobCard) {
    // Reload the document before any operation
    let doc = await frappe.db.get_doc('Job Card', jobCard);
    let qtyToManufacture = doc.for_quantity;
    let completedQty = doc.total_completed_qty || 0;
    let remainingQty = qtyToManufacture - completedQty;
    

    // Reload the document again before submitting
    doc = await frappe.db.get_doc('Job Card', jobCard);
    
    // If the job card is not already completed, update its status and completed quantity
    if (doc.status !== 'Completed') {
        let newCompletedQty = remainingQty;
        let totalCompletedQty = completedQty + newCompletedQty;

        // Set for_quantity to total_completed_qty before making the time log
        await frappe.db.set_value('Job Card', jobCard, {
            'for_quantity': totalCompletedQty
        });

        await frappe.call({
            method: "erpnext.manufacturing.doctype.job_card.job_card.make_time_log",
            args: {
                args: {
                    job_card_id: jobCard,
                    complete_time: frappe.datetime.now_datetime(),
                    completed_qty: newCompletedQty,
                    status: 'Completed'
                }
            }
        });

        await frappe.db.set_value('Job Card', jobCard, {
            'status': 'Completed',
            'total_completed_qty': totalCompletedQty
        });
    }

    // Reload the document before saving
    doc = await frappe.db.get_doc('Job Card', jobCard);

    try {
        await frappe.call({
            method: 'frappe.client.submit',
            args: {
                doc: doc
            }
        });

        frappe.show_alert({ message: __('Job Card submitted.'), indicator: 'green' });
        
        if (remainingQty > 0) {
            createNewJobCard(frm, doc, remainingQty);
        } else {
            refreshJobCards(frm);
        }
    } catch (error) {
        console.error("Error saving Job Card:", error);
        frappe.msgprint(__("Error saving Job Card. The job card list will be refreshed."));
        refreshJobCards(frm);
    }
}

async function createNewJobCard(frm, parentJobCard, remainingQty) {
    try {
        let result = await frappe.call({
            method: "aqiq_production_operations.aqiq_production_operations.rest.rest.create_and_rename_job_card",
            args: {
                parent_job_card: parentJobCard.name,
                remaining_qty: remainingQty
            }
        });

        if (result && result.message) {
            frappe.show_alert({ message: __(`New Job Card ${result.message} created for remaining quantity.`), indicator: 'green' });
            refreshJobCards(frm);
        } else {
            frappe.msgprint(__("Error creating new Job Card. Please try again."));
            refreshJobCards(frm);
        }
    } catch (error) {
        console.error("Error in createNewJobCard:", error);
        frappe.msgprint(__("An error occurred while creating a new Job Card. Please try again."));
        refreshJobCards(frm);
    }
}
function addJobCardActions(frm, jobCards) {
    frm.page.clear_actions_menu();

    const hasOpenJobs = jobCards.some(job => job.status === "Open");
    const hasRunningJobs = jobCards.some(job => job.status === "Work In Progress");

    if (hasOpenJobs) {
        frm.page.add_action_item(__('Start All Open Jobs'), () => startAllOpenJobs(frm, jobCards));
    }

    if (hasRunningJobs) {
        frm.page.add_action_item(__('Pause All Running Jobs'), () => pauseAllRunningJobs(frm, jobCards));
    }

    if (hasRunningJobs) {
        frm.page.add_action_item(__('Pause All Running Jobs'), () => pauseAllRunningJobs(frm, jobCards));
    }

    frm.page.add_action_item(__('Refresh Job Cards'), () => refreshJobCards(frm));
    frm.page.add_action_item(__('Clear All Filters'), () => clearAllFilters(frm));
}

function updateFilterIndicator(frm) {
    const allStatuses = ['Open', 'Work In Progress', 'On Hold', 'Completed', 'Cancelled'];
    const selectedStatuses = frm.doc.job_card_status || [];
    const filteredWorkstations = frm.doc.filtered_workstations ? frm.doc.filtered_workstations.split(',') : [];

    let indicatorText = '';
    let indicatorColor = 'blue';
    let tooltipText = '';

    if (selectedStatuses.length === allStatuses.length && filteredWorkstations.length === 0) {
        indicatorText = __('No Filters');
    } else {
        let filterParts = [];

        if (selectedStatuses.length !== allStatuses.length) {
            let statusText = truncateList(selectedStatuses, 2);
            filterParts.push(`<i class="fa fa-filter"></i> ${__(`Status: ${statusText}`)}`);
            tooltipText += `Statuses: ${selectedStatuses.join(', ')}\n`;
        }

        if (filteredWorkstations.length > 0) {
            let workstationText = truncateList(filteredWorkstations, 2);
            filterParts.push(`<i class="fa fa-cog"></i> ${__(`Workstation: ${workstationText}`)}`);
            tooltipText += `Workstations: ${filteredWorkstations.join(', ')}`;
        }

        indicatorText = __('Filtered: ') + filterParts.join(' | ');
        indicatorColor = 'orange';
    }

    frm.page.set_indicator(indicatorText, indicatorColor);
    frm.page.indicator.attr('title', tooltipText).tooltip();
}

function truncateList(list, maxItems) {
    return list.length <= maxItems ? list.join(', ') : `${list.slice(0, maxItems).join(', ')}, ...and ${list.length - maxItems} more`;
}

function clearAllFilters(frm) {
    frm.doc.job_card_status = ['Open', 'Work In Progress', 'On Hold', 'Completed', 'Cancelled', 'Material Transferred'];
    frm.doc.filtered_workstations = '';
    saveFiltersToServer(frm);
    refreshJobCards(frm);
}

function startAllOpenJobs(frm, jobCards) {
    jobCards.filter(job => job.status === "Open").forEach(job => startJob(frm, job.name));
}

function pauseAllRunningJobs(frm, jobCards) {
    jobCards.filter(job => job.status === "Work In Progress").forEach(job => pauseJob(frm, job.name));
    refreshJobCards(frm);
}
async function startJob(frm, jobCard) {
    try {
        // Fetch job card details
        const jobCardResponse = await frappe.call({
            method: "frappe.client.get",
            args: {
                doctype: "Job Card",
                name: jobCard
            }
        });

        if (jobCardResponse.message) {
            const jobCardDoc = jobCardResponse.message;

            // Validate sequence ID using the custom whitelisted method
            const validationResponse = await frappe.call({
                method: "aqiq_production_operations.aqiq_production_operations.rest.rest.validate_job_card_sequence_id",
                args: {
                    job_card_name: jobCard
                }
            });

            if (!validationResponse.exc) {
                let selectedEmployees;

                // Check if custom_employee_list is empty
                if (!jobCardDoc.custom_employee_list || jobCardDoc.custom_employee_list.length === 0) {
                    // If empty, prompt for employee selection
                    selectedEmployees = await selectEmployees(jobCardDoc);
                    
                    if (selectedEmployees.length === 0) {
                        frappe.msgprint(__("No employees selected. Job start aborted."));
                        return;
                    }
                } else {
                    // If not empty, use existing employees
                    selectedEmployees = jobCardDoc.custom_employee_list.map(emp => ({ employee: emp.employee }));
                }

                // Proceed with job start process
                await startJobProcess(frm, jobCard, selectedEmployees);
            } else {
                frappe.msgprint(__("Sequence ID validation failed. Job start aborted."));
            }
        }
    } catch (error) {
        console.error(error);
        frappe.msgprint(__("Error selecting employees or starting the job. Please try again."));
    }
}

async function startJobProcess(frm, jobCard, selectedEmployees) {
    try {
        // Prepare arguments for server-side method
        const args = {
            job_card_id: jobCard,
            start_time: frappe.datetime.now_datetime()
        };

        // Start the job with a single time log
        const timeLogResponse = await frappe.call({
            method: "erpnext.manufacturing.doctype.job_card.job_card.make_time_log",
            args: { args: JSON.stringify(args) }
        });

        if (!timeLogResponse.exc) {
            frappe.show_alert(__('Job Card started'));

            // Update the job card fields directly
            const updateResponse = await frappe.call({
                method: "frappe.client.set_value",
                args: {
                    doctype: "Job Card",
                    name: jobCard,
                    fieldname: {
                        status: "Work In Progress",
                        custom_is_active: 1,
                        custom_employee_list: selectedEmployees
                    }
                }
            });

            if (!updateResponse.exc) {
                refreshJobCards(frm);
            } else {
                frappe.msgprint(__("Error updating Job Card fields. Please try again."));
            }
        } else {
            frappe.msgprint(__("Error starting the job. Please try again."));
        }
    } catch (error) {
        console.error(error);
        frappe.msgprint(__("Error processing the job. Please try again."));
    }
}

function selectEmployees(jobCardDoc) {
    return new Promise((resolve, reject) => {
        frappe.call({
            method: "aqiq_production_operations.aqiq_production_operations.rest.rest.get_workstation_employees",
            args: {
                workstation: jobCardDoc.workstation
            },
            callback: function(r) {
                if (r.message && r.message.length > 0) {
                    const employees = r.message;
                    const d = new frappe.ui.Dialog({
                        title: __('Select Employees'),
                        fields: [
                            {
                                fieldname: 'employee_table',
                                fieldtype: 'Table',
                                label: __('Employees'),
                                fields: [
                                    {
                                        fieldname: 'employee',
                                        fieldtype: 'Link',
                                        options: 'Employee',
                                        label: __('Employee'),
                                        in_list_view: 1,                                       
                                    },
                                    {
                                        fieldname: 'employee_name',
                                        fieldtype: 'Data',
                                        label: __('Employee Name'),
                                        in_list_view: 1,
                                        read_only: 1
                                    }
                                ],
                                data: employees
                            }
                        ],
                        primary_action_label: __('Start Job'),
                        primary_action(values) {
                            const selectedEmployees = values.employee_table.filter(row => row.employee);
                            if (selectedEmployees.length > 0) {
                                d.hide();
                                resolve(selectedEmployees.map(emp => ({ employee: emp.employee })));
                            } else {
                                frappe.msgprint(__("Please select at least one employee."));
                                resolve([]);
                            }
                        }
                    });
                    d.show();
                } else {
                    frappe.msgprint(__("No employees found for this workstation. Please add employees to the workstation first."));
                    resolve([]);
                }
            }
        });
    });
}


async function pauseJob(frm, jobCard) {
    try {
        // Prepare the time log arguments
        const timeLogArgs = {
            job_card_id: jobCard,
            completed_qty: 0,
            complete_time: frappe.datetime.now_datetime()
        };

        // Make a single time log for the job card
        await frappe.call({
            method: "erpnext.manufacturing.doctype.job_card.job_card.make_time_log",
            args: {
                args: JSON.stringify(timeLogArgs)
            }
        });

        // Update the job card fields directly
        await frappe.call({
            method: "frappe.client.set_value",
            args: {
                doctype: "Job Card",
                name: jobCard,
                fieldname: {
                    status: "On Hold",
                    custom_is_active: "0" 
                }
            }
        });

        // Refresh the job card list in the form
        refreshJobCards(frm);
        frappe.show_alert(__('Job Card paused and updated successfully.'));
    } catch (error) {
        frappe.msgprint(__('Failed to pause the job card. Please try again.'));
        console.error(error);
    }
}

async function resumeJob(frm, jobCard) {
    try {
        // Fetch job card details
        let response = await frappe.call({
            method: "frappe.client.get",
            args: {
                doctype: "Job Card",
                name: jobCard
            }
        });
        
        if (response.message) {
            const jobCardDoc = response.message;
            // Set the actual start date to now
            jobCardDoc.actual_start_date = frappe.datetime.now_datetime();
            
            // Save the updated job card
            await frappe.call({
                method: "frappe.client.save",
                args: {
                    doc: jobCardDoc
                }
            });

            // Make a single time log for the job card
            await frappe.call({
                method: "erpnext.manufacturing.doctype.job_card.job_card.make_time_log",
                args: {
                    args: JSON.stringify({
                        job_card_id: jobCard,
                        start_time: frappe.datetime.now_datetime()
                    })
                }
            });

            // Update job card status to "Work In Progress" and set custom_is_active
            await frappe.call({
                method: "frappe.client.set_value",
                args: {
                    doctype: "Job Card",
                    name: jobCard,
                    fieldname: {
                        status: "Work In Progress",
                        custom_is_active: "1"
                    }
                }
            });

            // Refresh the job card list in the form
            refreshJobCards(frm);
            
            frappe.show_alert(__('Job Card resumed successfully.'));
        }
    } catch (error) {
        frappe.msgprint(__('Failed to resume the job card. Please try again.'));
        console.error(error);
    }
}

async function updateJobCardStatus(frm, jobCard, status, isActive) {
    try {
        const response = await frappe.call({
            method: "aqiq_production_operations.aqiq_production_operations.rest.update_jobcard.update_job_card_status",
            args: {
                job_card: jobCard,
                status: status,
                is_active: isActive
            }
        });

        if (response.message.success) {
            frappe.show_alert({
                message: __("Job Card {0} status updated to {1}", [jobCard, status]),
                indicator: 'green'
            });
        } else {
            frappe.msgprint(__("Error updating Job Card status: {0}", [response.message.message]));
        }
        return response;
    } catch (error) {
        frappe.msgprint(__('Failed to update the job card status. Please try again.'));
        console.error(error);
        return { message: { success: false, message: error.message } };
    }
}



function getStatusColor(status) {
    const colors = {
        "Open": "#ffa00a",
        "Work In Progress": "#7575ff",
        "On Hold": "#f43",
        "Completed": "#28a745",
        "Cancelled": "#ff5858",
        "Material Transferred": "#5bc0de" // Light blue color for Material Transferred status
    };
    return colors[status] || "#d1d8dd";
}

function formatDateTime(dateTimeString) {
    return moment(dateTimeString).format('DD-MM-YYYY HH:mm:ss');
}

function addCustomCSS() {
    const style = `
        <style>
            .job-cards-grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
                gap: 20px;
            }
            .job-card-tile {
                border: 1px solid var(--border-color);
                border-radius: 8px;
                overflow: hidden;
                box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
                transition: all 0.3s ease;
                background-color: var(--card-bg);
            }
            .job-card-tile:hover {
                box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
            }
            .job-card-header {
                padding: 10px;
                color: white;
                font-weight: bold;
                display: flex;
                justify-content: space-between;
                align-items: center;
                transition: background-color 0.3s ease;
            }
            .job-card-body {
                padding: 15px;
                background-color: var(--card-bg);
                color: var(--text-color);
                transition: background-color 0.3s ease;
            }
            .job-card-body p {
                margin-bottom: 8px;
                opacity: 0.9;
                transition: opacity 0.3s ease;
            }
            .job-card-tile:hover .job-card-body p {
                opacity: 1;
            }
            .job-card-actions {
                padding: 10px;
                background-color: var(--card-bg);
                text-align: right;
            }
            .btn {
                margin-left: 5px;
                transition: all 0.3s ease;
            }
            .btn:hover {
                transform: scale(1.05);
            }
            .job-card-link, .work-order-link {
                color: var(--link-color);
                transition: color 0.3s ease;
            }
            .job-card-link:hover, .work-order-link:hover {
                color: var(--link-hover-color);
            }
            .job-cards-group {
                margin-bottom: 30px;
            }
            .job-cards-group h3 {
                margin-bottom: 15px;
                padding-bottom: 5px;
                border-bottom: 2px solid var(--border-color);
                color: var(--heading-color);
            }
            .active-job-card {
                border: 2px solid var(--primary-color);
            }
            .dark-theme .job-card-body {
                background-color: var(--gray-700);
                color: var(--gray-100);
            }
            .dark-theme .job-card-actions {
                background-color: var(--gray-800);
            }
            .dark-theme .job-card-tile {
                border-color: var(--gray-600);
            }
            .dark-theme .job-card-link, .dark-theme .work-order-link {
                color: var(--blue-400);
            }
            .dark-theme .job-card-link:hover, .dark-theme .work-order-link:hover {
                color: var(--blue-300);
            }
        </style>
    `;
    $(style).appendTo('head');
}

$(document).on('app_ready', function() {
    if (frappe.app) {
        frappe.app.on('logout', function() {
            logoutJobCardTool();
        });
    }
});

function logoutJobCardTool() {
    console.log("Logging out Job Card Tool");
    localStorage.removeItem('job_card_filters');
    localStorage.removeItem('logged_in_workstation');

    // Clear user filters on the server
    frappe.call({
        method: "aqiq_production_operations.aqiq_production_operations.rest.job_card_filters.clear_user_filters",
        callback: function(r) {
            if (r.message && r.message.success) {
                console.log("Job Card Tool filters cleared successfully");
            } else {
                console.error("Failed to clear Job Card Tool filters");
            }
        },
        error: function(err) {
            console.error("Error during Job Card Tool logout:", err);
        }
    });
}