// Copyright (c) 2024, RONOH and contributors
// For license information, please see license.txt

frappe.query_reports["Work Order"] = {
	"filters": [
        {
            "fieldname": "from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.add_months(frappe.datetime.get_today(), -1),
            "reqd": 1
        },
        {
            "fieldname": "to_date",
            "label": __("To Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.get_today(),
            "reqd": 1
        },
        {
            "fieldname": "work_order",
            "label": __("Work Order"),
            "fieldtype": "Link",
            "options": "Work Order"
        },
        {
            "fieldname": "production_item",
            "label": __("Production Item"),
            "fieldtype": "Link",
            "options": "Item"
        },
        {
            "fieldname": "operation",
            "label": __("Operation"),
            "fieldtype": "Link",
            "options": "Operation"
        },
        {
            "fieldname": "workstation",
            "label": __("Workstation"),
            "fieldtype": "Link",
            "options": "Workstation"
        },
        {
            "fieldname": "status",
            "label": __("Status"),
            "fieldtype": "Select",
            "options": [
                "",
                "Open",
                "Work In Progress",
                "Completed",
                "Cancelled"
            ]
        },
        {
            "fieldname": "employee",
            "label": __("Employee"),
            "fieldtype": "Link",
            "options": "Employee"
        }
    ],

    "formatter": function(value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);
        
        if (column.fieldname == "total_completed_qty" && data && data.for_quantity) {
            var completion_percent = (data.total_completed_qty / data.for_quantity) * 100;
            value = value + ` <span style="color:${completion_percent < 50 ? 'red' : 'green'}">
                (${completion_percent.toFixed(2)}%)</span>`;
        }
        
        return value;
    }
};
