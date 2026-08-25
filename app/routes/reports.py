from flask import Blueprint, render_template, request, redirect, url_for, session, send_file
from datetime import date
from app.services.report_service import generate_report_dataframe, export_report_csv, ALL_REPORT_COLUMNS
from app.utils.decorators import admin_required

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/')
@admin_required
def index():

    search_query = request.args.get('search', '').strip()
    mode_filter = request.args.get('mode', 'ALL').strip()
    selected_cols = request.args.getlist('cols')
    date_from_str = request.args.get('date_from', '').strip()
    date_to_str = request.args.get('date_to', '').strip()

    date_from = None
    date_to = None
    try:
        if date_from_str:
            date_from = date.fromisoformat(date_from_str)
        if date_to_str:
            date_to = date.fromisoformat(date_to_str)
    except ValueError:
        pass

    if not selected_cols:
        selected_cols = list(ALL_REPORT_COLUMNS.keys())

    df = generate_report_dataframe(selected_columns=selected_cols, search_query=search_query, mode_filter=mode_filter, date_from=date_from, date_to=date_to)

    records = df.to_dict(orient='records')
    headers = list(df.columns)

    return render_template(
        'reports/index.html',
        all_columns=ALL_REPORT_COLUMNS,
        selected_cols=selected_cols,
        headers=headers,
        records=records,
        search_query=search_query,
        mode_filter=mode_filter,
        date_from_str=date_from_str,
        date_to_str=date_to_str
    )


@reports_bp.route('/export_csv')
@admin_required
def export_csv():
    search_query = request.args.get('search', '').strip()
    mode_filter = request.args.get('mode', 'ALL').strip()
    selected_cols = request.args.getlist('cols')
    date_from_str = request.args.get('date_from', '').strip()
    date_to_str = request.args.get('date_to', '').strip()

    date_from = None
    date_to = None
    try:
        if date_from_str:
            date_from = date.fromisoformat(date_from_str)
        if date_to_str:
            date_to = date.fromisoformat(date_to_str)
    except ValueError:
        pass

    if not selected_cols:
        selected_cols = list(ALL_REPORT_COLUMNS.keys())

    df = generate_report_dataframe(selected_columns=selected_cols, search_query=search_query, mode_filter=mode_filter, date_from=date_from, date_to=date_to)
    csv_buffer = export_report_csv(df)

    return send_file(
        csv_buffer,
        mimetype='text/csv',
        as_attachment=True,
        download_name='Narayana_LND_Report.csv'
    )
