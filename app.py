from flask import Flask, render_template, jsonify, request, send_file
from datetime import datetime
import io
from openpyxl import Workbook

from scraper_selenium import FirmenABCSeleniumScraper

app = Flask(__name__)
selenium_scraper = FirmenABCSeleniumScraper()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/scrape-xlsx', methods=['POST'])
def scrape_xlsx():
    data = request.json or {}
    url = (data.get('url') or '').strip()
    max_pages = data.get('max_pages', 1)

    if not url:
        return jsonify({'error': 'URL megadása kötelező'}), 400

    try:
        result = selenium_scraper.scrape_listing_to_companies(url, max_pages=max_pages)

        columns = [
            'is_company',
            'name',
            'type',
            'country_id',
            'zip',
            'city',
            'street',
            'street2',
            'parent_id',
            'parent_id/id',
            'vat',
            'email',
            'phone',
            'lang',
            'category_id',
            'x_studio_oerp_teaor_code',
            'x_studio_oerp_teaor_description',
            'x_studio_oerp_net_annual_revenue',
            'x_studio_currency_id',
        ]
        headers = columns

        wb = Workbook()
        ws = wb.active
        ws.title = 'Companies'
        ws.append(headers)
        for c in result.companies:
            row = {
                'is_company': True,
                'name': c.get('name', ''),
                'type': '',
                'country_id': 'AT',
                'zip': c.get('zip', ''),
                'city': c.get('city', ''),
                'street': c.get('street', ''),
                'street2': '',
                'parent_id': '',
                'parent_id/id': '',
                'vat': c.get('vat_id', ''),
                'email': c.get('email', ''),
                'phone': c.get('phone', ''),
                'lang': 'hu_HU',
                'category_id': '',
                'x_studio_oerp_teaor_code': '',
                'x_studio_oerp_teaor_description': '',
                'x_studio_oerp_net_annual_revenue': '',
                'x_studio_currency_id': 'EUR',
            }
            ws.append([row.get(col, '') for col in columns])

        bytes_buffer = io.BytesIO()
        wb.save(bytes_buffer)
        bytes_buffer.seek(0)

        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M')
        filename = f'firmenabc_{timestamp}.xlsx'

        return send_file(
            bytes_buffer,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)
