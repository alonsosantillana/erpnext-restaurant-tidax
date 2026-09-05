POS_CLOSING_DOCTYPE = "POS Closing Entry"
POS_TRANSACTIONS_FIELD = "pos_transactions"


def append_pos_session_conditions(filters, conditions, invoice_alias="invoice"):
	"""Append optional POS opening/closing filters without multiplying invoice rows."""
	filters.pos_closing_doctype = POS_CLOSING_DOCTYPE
	filters.pos_transactions_field = POS_TRANSACTIONS_FIELD

	if filters.get("pos_opening_entry"):
		conditions.append(
			f"""
			(
				{invoice_alias}.restaurant_pos_opening_entry = %(pos_opening_entry)s
				OR EXISTS (
					SELECT 1
					FROM `tabPOS Invoice Reference` AS session_reference
					INNER JOIN `tabPOS Closing Entry` AS session_closing
						ON session_closing.name = session_reference.parent
					WHERE
						session_reference.pos_invoice = {invoice_alias}.name
						AND session_reference.parenttype = %(pos_closing_doctype)s
						AND session_reference.parentfield = %(pos_transactions_field)s
						AND session_closing.docstatus = 1
						AND session_closing.pos_opening_entry = %(pos_opening_entry)s
				)
			)
			"""
		)

	if filters.get("pos_closing_entry"):
		conditions.append(
			f"""
			EXISTS (
				SELECT 1
				FROM `tabPOS Invoice Reference` AS selected_reference
				INNER JOIN `tabPOS Closing Entry` AS selected_closing
					ON selected_closing.name = selected_reference.parent
				WHERE
					selected_reference.pos_invoice = {invoice_alias}.name
					AND selected_reference.parenttype = %(pos_closing_doctype)s
					AND selected_reference.parentfield = %(pos_transactions_field)s
					AND selected_closing.docstatus = 1
					AND selected_closing.name = %(pos_closing_entry)s
					AND selected_closing.company = {invoice_alias}.company
			)
			"""
		)

	return conditions
