"""Default HTML/CSS document templates for RFQ Letter, LOI, and PO."""

RFQ_LETTER_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body { font-family: 'Segoe UI', Arial, sans-serif; color: #1a1a1a; margin: 0; padding: 40px; font-size: 11pt; }
  .letterhead { border-bottom: 3px solid #1a3a5c; padding-bottom: 20px; margin-bottom: 30px; }
  .logo { max-height: 60px; margin-bottom: 10px; }
  .company-name { font-size: 18pt; font-weight: bold; color: #1a3a5c; }
  .company-details { font-size: 9pt; color: #555; margin-top: 5px; }
  .date { text-align: right; margin-bottom: 20px; font-size: 10pt; color: #555; }
  .recipient { margin-bottom: 20px; }
  .recipient-name { font-weight: bold; font-size: 11pt; }
  .subject { font-weight: bold; font-size: 12pt; margin: 20px 0 10px 0; color: #1a3a5c; }
  .body-text { line-height: 1.6; margin-bottom: 20px; }
  .substance-table { width: 100%; border-collapse: collapse; margin: 15px 0; }
  .substance-table th, .substance-table td { border: 1px solid #ccc; padding: 8px 12px; text-align: left; font-size: 10pt; }
  .substance-table th { background-color: #1a3a5c; color: white; }
  .questions { margin: 15px 0; }
  .questions li { margin-bottom: 5px; }
  .signature { margin-top: 40px; }
  .signature-line { border-top: 1px solid #333; width: 200px; padding-top: 5px; font-size: 10pt; }
  .footer { margin-top: 40px; border-top: 1px solid #ccc; padding-top: 10px; font-size: 8pt; color: #888; text-align: center; }
</style>
</head>
<body>
  <div class="letterhead">
    <div class="company-name">{{company_name}}</div>
    <div class="company-details">
      {{company_address}}<br>
      {% if company_registration %}Reg: {{company_registration}} | {% endif %}{% if company_vat %}VAT: {{company_vat}} | {% endif %}{% if company_eori %}EORI: {{company_eori}}{% endif %}
    </div>
  </div>

  <div class="date">{{date}}</div>

  <div class="recipient">
    <div class="recipient-name">{{supplier_name}}</div>
    <div>{{supplier_address}}</div>
  </div>

  <div class="subject">Request for Quotation — {{substance_name}} (CAS: {{cas}})</div>

  <div class="body-text">
    <p>Dear Sir/Madam,</p>
    <p>We are writing to request a quotation for the following chemical substance:</p>

    <table class="substance-table">
      <tr><th>Parameter</th><th>Details</th></tr>
      <tr><td>Substance</td><td>{{substance_name}}</td></tr>
      <tr><td>CAS Number</td><td>{{cas}}</td></tr>
      <tr><td>Molecular Formula</td><td>{{molecular_formula}}</td></tr>
      <tr><td>Quantity Required</td><td>{{quantity}}</td></tr>
      <tr><td>Required Grade / Purity</td><td>{{required_grade}}</td></tr>
      <tr><td>Destination</td><td>{{destination_country}}</td></tr>
      <tr><td>Intended Use</td><td>{{intended_use}}</td></tr>
    </table>

    <p>We would appreciate your best quotation including:</p>
    <ol class="questions">
      <li>Unit price and applicable Incoterms</li>
      <li>Minimum order quantity (MOQ)</li>
      <li>Lead time for delivery</li>
      <li>Available certifications (COA, SDS, REACH)</li>
      <li>Sample availability and pricing</li>
      <li>Payment terms</li>
      <li>Packaging specifications</li>
    </ol>

    <p>We look forward to your prompt response.</p>
  </div>

  <div class="signature">
    <div>Best regards,</div>
    <div class="signature-line">
      {{sender_name}}<br>
      {{sender_title}}<br>
      {{sender_department}}
    </div>
  </div>

  <div class="footer">{{letterhead_footer}}</div>
</body>
</html>"""

LOI_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body { font-family: 'Segoe UI', Arial, sans-serif; color: #1a1a1a; margin: 0; padding: 40px; font-size: 11pt; }
  .letterhead { border-bottom: 3px solid #1a3a5c; padding-bottom: 20px; margin-bottom: 30px; }
  .company-name { font-size: 18pt; font-weight: bold; color: #1a3a5c; }
  .company-details { font-size: 9pt; color: #555; margin-top: 5px; }
  .date { text-align: right; margin-bottom: 20px; font-size: 10pt; color: #555; }
  .title { font-size: 14pt; font-weight: bold; text-align: center; color: #1a3a5c; margin: 20px 0; text-transform: uppercase; }
  .body-text { line-height: 1.6; margin-bottom: 20px; }
  .detail-table { width: 100%; border-collapse: collapse; margin: 15px 0; }
  .detail-table th, .detail-table td { border: 1px solid #ccc; padding: 8px 12px; text-align: left; font-size: 10pt; }
  .detail-table th { background-color: #1a3a5c; color: white; width: 35%; }
  .signature-block { display: flex; justify-content: space-between; margin-top: 50px; }
  .signature-line { border-top: 1px solid #333; width: 200px; padding-top: 5px; font-size: 10pt; margin-top: 60px; }
  .footer { margin-top: 40px; border-top: 1px solid #ccc; padding-top: 10px; font-size: 8pt; color: #888; text-align: center; }
</style>
</head>
<body>
  <div class="letterhead">
    <div class="company-name">{{company_name}}</div>
    <div class="company-details">
      {{company_address}}<br>
      {% if company_registration %}Reg: {{company_registration}} | {% endif %}{% if company_vat %}VAT: {{company_vat}} | {% endif %}{% if company_eori %}EORI: {{company_eori}}{% endif %}
    </div>
  </div>

  <div class="date">{{date}}</div>

  <div class="title">Letter of Intent</div>

  <div class="body-text">
    <p>This Letter of Intent ("LOI") sets forth the basic terms under which <strong>{{company_name}}</strong> ("Buyer") intends to purchase chemical products from <strong>{{supplier_name}}</strong> ("Seller").</p>

    <table class="detail-table">
      <tr><th>Product</th><td>{{substance_name}}</td></tr>
      <tr><th>CAS Number</th><td>{{cas}}</td></tr>
      <tr><th>Quantity</th><td>{{quantity}}</td></tr>
      <tr><th>Unit Price</th><td>{{price}} {{currency}}</td></tr>
      <tr><th>Total Value (est.)</th><td>{{total_value}} {{currency}}</td></tr>
      <tr><th>Incoterms</th><td>{{incoterms}}</td></tr>
      <tr><th>Quality / Grade</th><td>{{required_grade}}</td></tr>
      <tr><th>Destination</th><td>{{destination_country}}</td></tr>
      <tr><th>Lead Time</th><td>{{lead_time}}</td></tr>
      <tr><th>Payment Terms</th><td>{{payment_terms}}</td></tr>
    </table>

    <p><strong>Terms and Conditions:</strong></p>
    <ol>
      <li>This LOI is non-binding and subject to final contract negotiation.</li>
      <li>The Buyer reserves the right to request product samples and certificates of analysis (COA) before final commitment.</li>
      <li>Both parties agree to comply with all applicable regulations including REACH, CLP, and local import/export requirements.</li>
      <li>A formal Purchase Order will be issued upon satisfactory sample evaluation and contract agreement.</li>
      <li>This LOI is valid for 30 days from the date of issuance.</li>
    </ol>
  </div>

  <div class="signature-block">
    <div>
      <strong>For the Buyer:</strong>
      <div class="signature-line">
        {{sender_name}}<br>
        {{sender_title}}
      </div>
    </div>
    <div>
      <strong>For the Seller:</strong>
      <div class="signature-line">
        {{supplier_name}}<br>
        Authorized Signatory
      </div>
    </div>
  </div>

  <div class="footer">{{letterhead_footer}}</div>
</body>
</html>"""

PO_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body { font-family: 'Segoe UI', Arial, sans-serif; color: #1a1a1a; margin: 0; padding: 40px; font-size: 11pt; }
  .letterhead { border-bottom: 3px solid #1a3a5c; padding-bottom: 20px; margin-bottom: 30px; }
  .company-name { font-size: 18pt; font-weight: bold; color: #1a3a5c; }
  .company-details { font-size: 9pt; color: #555; margin-top: 5px; }
  .po-header { display: flex; justify-content: space-between; margin-bottom: 25px; }
  .po-number { font-size: 14pt; font-weight: bold; color: #1a3a5c; }
  .date { font-size: 10pt; color: #555; }
  .title { font-size: 16pt; font-weight: bold; text-align: center; color: #1a3a5c; margin: 10px 0 25px 0; text-transform: uppercase; border: 2px solid #1a3a5c; padding: 8px; }
  .parties { display: flex; gap: 40px; margin-bottom: 20px; }
  .party { flex: 1; }
  .party-title { font-weight: bold; font-size: 10pt; color: #1a3a5c; border-bottom: 1px solid #ccc; padding-bottom: 3px; margin-bottom: 5px; }
  .detail-table { width: 100%; border-collapse: collapse; margin: 15px 0; }
  .detail-table th, .detail-table td { border: 1px solid #ccc; padding: 8px 12px; text-align: left; font-size: 10pt; }
  .detail-table th { background-color: #1a3a5c; color: white; }
  .resp-table { width: 100%; border-collapse: collapse; margin: 10px 0; font-size: 9pt; }
  .resp-table th, .resp-table td { border: 1px solid #ddd; padding: 5px 10px; }
  .resp-table th { background-color: #f0f4f8; }
  .buyer { background-color: #e8f5e9; }
  .seller { background-color: #e3f2fd; }
  .section-title { font-weight: bold; font-size: 11pt; color: #1a3a5c; margin: 20px 0 8px 0; border-bottom: 1px solid #ddd; padding-bottom: 3px; }
  .body-text { line-height: 1.5; }
  .signature-block { display: flex; justify-content: space-between; margin-top: 40px; }
  .signature-line { border-top: 1px solid #333; width: 200px; padding-top: 5px; font-size: 10pt; margin-top: 60px; }
  .footer { margin-top: 40px; border-top: 1px solid #ccc; padding-top: 10px; font-size: 8pt; color: #888; text-align: center; }
</style>
</head>
<body>
  <div class="letterhead">
    <div class="company-name">{{company_name}}</div>
    <div class="company-details">
      {{company_address}}<br>
      {% if company_registration %}Reg: {{company_registration}} | {% endif %}{% if company_vat %}VAT: {{company_vat}} | {% endif %}{% if company_eori %}EORI: {{company_eori}}{% endif %}
    </div>
  </div>

  <div class="po-header">
    <div>
      <div class="po-number">PO Number: {{po_number}}</div>
      <div>Date: {{date}}</div>
    </div>
    <div style="text-align: right;">
      <div>Reference Quote: {{quote_reference}}</div>
      <div>Validity: 30 days</div>
    </div>
  </div>

  <div class="title">Purchase Order</div>

  <div class="parties">
    <div class="party">
      <div class="party-title">BUYER</div>
      <strong>{{company_name}}</strong><br>
      {{company_address}}<br>
      Attn: {{sender_name}}, {{sender_title}}
    </div>
    <div class="party">
      <div class="party-title">SELLER</div>
      <strong>{{supplier_name}}</strong><br>
      {{supplier_address}}<br>
      {{supplier_country}}
    </div>
  </div>

  <div class="section-title">1. Order Details</div>
  <table class="detail-table">
    <tr><th style="width:30%">Product</th><td>{{substance_name}}</td></tr>
    <tr><th>CAS Number</th><td>{{cas}}</td></tr>
    <tr><th>Molecular Formula</th><td>{{molecular_formula}}</td></tr>
    <tr><th>Quantity</th><td>{{quantity}}</td></tr>
    <tr><th>Unit Price</th><td>{{price}} {{currency}} / {{unit}}</td></tr>
    <tr><th>Total Amount</th><td><strong>{{total_value}} {{currency}}</strong></td></tr>
    <tr><th>Quality / Grade</th><td>{{required_grade}}</td></tr>
    <tr><th>Packaging</th><td>{{packaging}}</td></tr>
  </table>

  <div class="section-title">2. Delivery & Transport</div>
  <table class="detail-table">
    <tr><th style="width:30%">Transport Type</th><td>{{transport_type}}</td></tr>
    <tr><th>Incoterms {{year}}</th><td><strong>{{incoterms}}</strong></td></tr>
    <tr><th>Destination</th><td>{{delivery_address}}</td></tr>
    <tr><th>Lead Time</th><td>{{lead_time}}</td></tr>
    <tr><th>Payment Terms</th><td>{{payment_terms}}</td></tr>
  </table>

  <div class="section-title">3. Incoterms Responsibility Matrix ({{incoterms}})</div>
  <table class="resp-table">
    <tr><th>Cost / Responsibility</th><th>Buyer</th><th>Seller</th></tr>
    {{responsibility_matrix_rows}}
  </table>

  <div class="section-title">4. Customs & Tariff Information</div>
  <table class="detail-table">
    <tr><th style="width:30%">HS Code</th><td>{{hs_code}}</td></tr>
    <tr><th>Import Duty Rate</th><td>{{duty_rate}}</td></tr>
    <tr><th>Preferential Rate</th><td>{{preferential_rate}}</td></tr>
    <tr><th>Customs Description</th><td>{{customs_description}}</td></tr>
    <tr><th>Legal Use / Purpose</th><td>{{legal_use_description}}</td></tr>
  </table>

  {% if special_instructions %}
  <div class="section-title">5. Special Instructions</div>
  <div class="body-text">{{special_instructions}}</div>
  {% endif %}

  <div class="section-title">General Conditions</div>
  <div class="body-text" style="font-size: 9pt;">
    <ol>
      <li>Goods must comply with REACH, CLP, and applicable local regulations.</li>
      <li>COA, SDS, and all required documentation must accompany shipment.</li>
      <li>Quality disputes subject to independent laboratory analysis.</li>
      <li>This PO is subject to the terms of the preceding LOI / agreement between the parties.</li>
    </ol>
  </div>

  <div class="signature-block">
    <div>
      <strong>Authorized by Buyer:</strong>
      <div class="signature-line">
        {{sender_name}}<br>
        {{sender_title}}<br>
        Date: {{date}}
      </div>
    </div>
    <div>
      <strong>Accepted by Seller:</strong>
      <div class="signature-line">
        {{supplier_name}}<br>
        Authorized Signatory<br>
        Date: _______________
      </div>
    </div>
  </div>

  <div class="footer">{{letterhead_footer}}</div>
</body>
</html>"""
