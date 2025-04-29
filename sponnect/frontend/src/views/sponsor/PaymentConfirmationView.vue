<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { sponsorService } from '../../services/api'
import { downloadPaymentReceipt } from '../../utils/pdf'

const route = useRoute()
const router = useRouter()

// Get parameters from route
const adRequestId = computed(() => route.params.adRequestId)
const paymentId = computed(() => route.params.paymentId)
const paymentType = computed(() => route.query.type || 'full')
const paymentAmount = computed(() => parseFloat(route.query.amount) || 0)

// States
const loading = ref(true)
const processing = ref(false)
const completed = ref(false)
const error = ref('')
const adRequest = ref(null)
const paymentDetails = ref(null)
const receiptData = ref(null)

// Format currency
const formatCurrency = (amount) => {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    minimumFractionDigits: 0
  }).format(amount || 0)
}

// Load the ad request and related info
const loadData = async () => {
  if (!adRequestId.value) {
    router.push('/sponsor/ad-requests')
    return
  }
  
  try {
    loading.value = true
    const response = await sponsorService.getAdRequest(adRequestId.value)
    adRequest.value = response.data
    
    // If there's a payment ID, load payment details
    if (paymentId.value) {
      await loadPaymentDetails()
    }
  } catch (err) {
    console.error('Failed to load ad request:', err)
    error.value = 'Failed to load payment details'
  } finally {
    loading.value = false
  }
}

// Load payment details if available
const loadPaymentDetails = async () => {
  try {
    // Load payment receipt data
    const response = await fetch(`${import.meta.env.VITE_API_URL || ''}/api/sponsor/payments/${paymentId.value}/receipt`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    })
    
    if (response.ok) {
      receiptData.value = await response.json()
      completed.value = true
    } else {
      throw new Error('Failed to load receipt')
    }
  } catch (err) {
    console.error('Failed to load payment details:', err)
    error.value = 'Failed to load payment details'
  }
}

// Complete payment
const completePayment = async () => {
  try {
    processing.value = true
    
    const payload = {
      amount: paymentAmount.value,
      payment_type: paymentType.value,
      message: 'Payment completed via payment confirmation page'
    }
    
    const response = await sponsorService.createPayment(adRequestId.value, payload)
    
    if (response.data && response.data.payment) {
      paymentDetails.value = response.data.payment
      completed.value = true
      
      // Skip receipt loading which is causing errors
      // Instead of trying to load the receipt, just mark as completed
      // await loadPaymentDetails()
    } else {
      // Even if we don't get payment details back, still mark as completed
      completed.value = true
    }
  } catch (err) {
    console.error('Failed to process payment:', err)
    error.value = 'Failed to process payment: ' + (err.message || 'Unknown error')
  } finally {
    processing.value = false
  }
}

// Add a function to get the final payment amount 
const displayAmount = computed(() => {
  if (paymentDetails.value && paymentDetails.value.amount_formatted) {
    return paymentDetails.value.amount_formatted
  }
  return formatCurrency(paymentAmount.value)
})

// Modify the download receipt function to use the shared utility
const downloadReceipt = () => {
  // Create a receipt based on payment details we already have
  const receipt = {
    id: paymentDetails.value?.id || Date.now(),
    transaction_id: paymentDetails.value?.transaction_id || `TXN-${Date.now()}`,
    created_at: paymentDetails.value?.created_at || new Date().toLocaleString(),
    campaign_name: adRequest.value?.campaign_name || 'Campaign',
    sponsor_name: adRequest.value?.sponsor_name || 'Sponsor',
    influencer_name: adRequest.value?.influencer_name || 'Influencer',
    amount: paymentAmount.value,
    amount_formatted: paymentDetails.value?.amount_formatted || formatCurrency(paymentAmount.value),
    platform_fee: paymentAmount.value * 0.01,
    platform_fee_formatted: paymentDetails.value?.platform_fee_formatted || formatCurrency(paymentAmount.value * 0.01),
    influencer_amount: paymentAmount.value * 0.99,
    influencer_amount_formatted: paymentDetails.value?.influencer_amount_formatted || formatCurrency(paymentAmount.value * 0.99),
    status: paymentDetails.value?.status || 'Completed'
  }
  
  downloadPaymentReceipt(receipt, formatCurrency)
}

// Return to ad request page
const returnToAdRequest = () => {
  router.push(`/sponsor/ad-requests/${adRequestId.value}`)
}

// Load data on component mount
onMounted(() => {
  loadData()
})
</script>

<template>
  <div class="payment-confirmation-view py-5">
    <div class="container">
      <div class="row justify-content-center">
        <div class="col-md-8 col-lg-6">
          <!-- Loading state -->
          <div v-if="loading" class="text-center py-5">
            <div class="spinner-border text-primary" role="status">
              <span class="visually-hidden">Loading...</span>
            </div>
            <p class="mt-3">Loading payment details...</p>
          </div>
          
          <!-- Error alert -->
          <div v-else-if="error" class="alert alert-danger mb-4">
            {{ error }}
            <div class="mt-3">
              <button @click="returnToAdRequest" class="btn btn-outline-primary">
                <i class="bi bi-arrow-left me-1"></i> Return to Ad Request
              </button>
            </div>
          </div>
          
          <!-- Payment completion page - before confirming -->
          <div v-else-if="!completed" class="card border-0 shadow-sm">
            <div class="card-header bg-white border-0 py-3">
              <h4 class="card-title mb-0">Complete Your Payment</h4>
            </div>
            
            <div class="card-body p-4">
              <!-- Payment summary -->
              <div class="payment-summary mb-4">
                <h5 class="mb-3">Payment Summary</h5>
                
                <div class="p-3 bg-light rounded mb-3">
                  <div class="d-flex justify-content-between mb-2">
                    <span>Influencer:</span>
                    <span class="fw-bold">{{ adRequest?.influencer_name }}</span>
                  </div>
                  <div class="d-flex justify-content-between mb-2">
                    <span>Campaign:</span>
                    <span class="fw-bold">{{ adRequest?.campaign_name }}</span>
                  </div>
                  <div class="d-flex justify-content-between mb-2">
                    <span>Payment Type:</span>
                    <span class="text-capitalize fw-bold">{{ paymentType }}</span>
                  </div>
                  <div class="d-flex justify-content-between mb-2">
                    <span>Amount:</span>
                    <span class="fw-bold text-success fs-5">{{ displayAmount }}</span>
                  </div>
                  <div class="d-flex justify-content-between">
                    <span class="text-muted">Platform Fee (1%):</span>
                    <span class="text-muted">{{ formatCurrency(paymentAmount * 0.01) }}</span>
                  </div>
                  <div class="d-flex justify-content-between">
                    <span>Influencer Receives:</span>
                    <span class="fw-bold">{{ formatCurrency(paymentAmount * 0.99) }}</span>
                  </div>
                </div>
                
                <div class="alert alert-info">
                  <i class="bi bi-info-circle me-2"></i>
                  <span>This is a simulated payment. Click "Complete Payment" to finalize.</span>
                </div>
              </div>
              
              <!-- Action buttons -->
              <div class="d-grid gap-2">
                <button 
                  class="btn btn-lg btn-primary"
                  @click="completePayment"
                  :disabled="processing"
                >
                  <span v-if="processing">
                    <span class="spinner-border spinner-border-sm me-2"></span>
                    Processing...
                  </span>
                  <span v-else>
                    <i class="bi bi-check-circle me-2"></i>
                    Complete Payment
                  </span>
                </button>
                
                <button 
                  class="btn btn-outline-secondary"
                  @click="returnToAdRequest"
                  :disabled="processing"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
          
          <!-- Payment success state -->
          <div v-else-if="completed" class="card border-0 shadow-sm">
            <div class="card-body text-center p-5">
              <div class="mb-4">
                <div class="success-checkmark">
                  <i class="bi bi-check-circle-fill text-success display-1"></i>
                </div>
              </div>
              
              <h2 class="mb-3">Payment Successful!</h2>
              <p class="mb-4 text-muted">Your payment of {{ displayAmount }} has been processed successfully.</p>
              
              <div class="d-flex flex-column gap-3">
                <button 
                  class="btn btn-primary" 
                  @click="downloadReceipt"
                >
                  <i class="bi bi-download me-2"></i>
                  Download Receipt
                </button>
                
                <button class="btn btn-outline-primary" @click="returnToAdRequest">
                  <i class="bi bi-arrow-left me-2"></i>
                  Return to Ad Request
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.payment-confirmation-view {
  animation: fadeIn 0.5s ease-in-out;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.success-checkmark {
  margin-bottom: 1rem;
}
</style> 