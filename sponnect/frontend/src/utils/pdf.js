import jsPDF from 'jspdf'

/**
 * Generate a PDF payment receipt
 * @param {Object} data - Receipt data
 * @param {string} data.receipt_id - Receipt ID
 * @param {string} data.transaction_id - Transaction ID
 * @param {string} data.date - Payment date
 * @param {string} data.campaign_name - Campaign name
 * @param {string} data.sponsor_name - Sponsor name
 * @param {string} data.influencer_name - Influencer name
 * @param {string} data.amount_formatted_pdf - PDF-friendly formatted payment amount
 * @param {string} data.platform_fee_formatted_pdf - PDF-friendly formatted platform fee
 * @param {string} data.influencer_amount_formatted_pdf - PDF-friendly formatted influencer amount
 * @param {string} data.status - Payment status
 * @returns {jsPDF} PDF document
 */
export const generatePaymentReceipt = (data) => {
  // Create PDF document
  const doc = new jsPDF();
  
  // Set PDF metadata
  doc.setProperties({
    title: `Payment Receipt - ${data.receipt_id}`,
    subject: 'Payment Receipt',
    author: 'Sponnect Platform',
    creator: 'Sponnect'
  });
  
  // Add logo/header
  doc.setFontSize(22);
  doc.setTextColor(41, 128, 185); // Blue color
  doc.text('Payment Receipt', 105, 20, { align: 'center' });
  
  doc.setFontSize(12);
  doc.setTextColor(100, 100, 100); // Grey
  doc.text('Sponnect Platform', 105, 27, { align: 'center' });
  
  // Add receipt details
  doc.setLineWidth(0.5);
  doc.line(20, 35, 190, 35); // Draw a horizontal line
  
  // Set font for receipt text
  doc.setFontSize(10);
  doc.setTextColor(0, 0, 0); // Black
  
  // Receipt details
  doc.setFont(undefined, 'bold');
  doc.text('Receipt ID:', 20, 45);
  doc.setFont(undefined, 'normal');
  doc.text(data.receipt_id, 70, 45);
  
  doc.setFont(undefined, 'bold');
  doc.text('Transaction ID:', 20, 52);
  doc.setFont(undefined, 'normal');
  doc.text(data.transaction_id, 70, 52);
  
  doc.setFont(undefined, 'bold');
  doc.text('Date:', 20, 59);
  doc.setFont(undefined, 'normal');
  doc.text(data.date, 70, 59);
  
  // Campaign & user details
  doc.line(20, 65, 190, 65); // Draw a horizontal line
  
  doc.setFont(undefined, 'bold');
  doc.text('Campaign:', 20, 75);
  doc.setFont(undefined, 'normal');
  doc.text(data.campaign_name, 70, 75);
  
  doc.setFont(undefined, 'bold');
  doc.text('Sponsor:', 20, 82);
  doc.setFont(undefined, 'normal');
  doc.text(data.sponsor_name, 70, 82);
  
  doc.setFont(undefined, 'bold');
  doc.text('Influencer:', 20, 89);
  doc.setFont(undefined, 'normal');
  doc.text(data.influencer_name, 70, 89);
  
  // Payment details
  doc.line(20, 95, 190, 95); // Draw a horizontal line
  
  doc.setFont(undefined, 'bold');
  doc.text('Payment Amount:', 20, 105);
  doc.setFont(undefined, 'normal');
  doc.text(data.amount_formatted_pdf || data.amount_formatted, 70, 105);
  
  doc.setFont(undefined, 'bold');
  doc.text('Platform Fee (1%):', 20, 112);
  doc.setFont(undefined, 'normal');
  doc.text(data.platform_fee_formatted_pdf || data.platform_fee_formatted, 70, 112);
  
  doc.setFont(undefined, 'bold');
  doc.text('Influencer Amount:', 20, 119);
  doc.setFont(undefined, 'normal');
  doc.text(data.influencer_amount_formatted_pdf || data.influencer_amount_formatted, 70, 119);
  
  doc.setFont(undefined, 'bold');
  doc.text('Status:', 20, 126);
  doc.setFont(undefined, 'normal');
  doc.text(data.status, 70, 126);
  
  // Footer
  doc.setFontSize(8);
  doc.setTextColor(100, 100, 100); // Grey
  doc.text('Thank you for using Sponnect!', 105, 250, { align: 'center' });
  doc.text('This is a computer-generated receipt and does not require a signature.', 105, 255, { align: 'center' });
  
  return doc;
}

/**
 * Format currency for PDF (fallback if PDF-friendly format not provided)
 * @param {number} amount - Amount to format
 * @returns {string} Formatted amount
 */
const formatCurrencyForPDF = (amount) => {
  if (amount === null || amount === undefined) return '';
  return `Rs. ${amount.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

/**
 * Download a payment receipt as PDF
 * @param {Object} payment - Payment object
 * @param {function} formatCurrency - Function to format currency
 */
export const downloadPaymentReceipt = (payment, formatCurrency) => {
  const receipt = {
    receipt_id: `RCPT-${payment.id || Date.now()}`,
    transaction_id: payment.transaction_id || `TXN-${Date.now()}`,
    date: payment.created_at || new Date().toLocaleString(),
    campaign_name: payment.campaign_name || 'Campaign',
    sponsor_name: payment.sponsor_name || 'Sponsor',
    influencer_name: payment.influencer_name || 'Influencer',
    // Use PDF-friendly formats if available, otherwise fall back to standard formats or generate them
    amount_formatted: payment.amount_formatted || formatCurrency(payment.amount || 0),
    amount_formatted_pdf: payment.amount_formatted_pdf || formatCurrencyForPDF(payment.amount || 0),
    platform_fee_formatted: payment.platform_fee_formatted || formatCurrency(payment.platform_fee || 0),
    platform_fee_formatted_pdf: payment.platform_fee_formatted_pdf || formatCurrencyForPDF(payment.platform_fee || 0),
    influencer_amount_formatted: payment.influencer_amount_formatted || formatCurrency(payment.influencer_amount || 0),
    influencer_amount_formatted_pdf: payment.influencer_amount_formatted_pdf || formatCurrencyForPDF(payment.influencer_amount || 0),
    status: payment.status || 'Completed'
  }
  
  const doc = generatePaymentReceipt(receipt);
  
  // Save the PDF with a filename
  doc.save(`receipt-${receipt.receipt_id}.pdf`);
} 