<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { sponsorService } from '../../services/api'

const route = useRoute()
const router = useRouter()

// Get parameters from the route
const adRequestId = computed(() => route.params.adRequestId)
const amount = computed(() => route.query.amount || 0)

// States
const loading = ref(false)
const processingPayment = ref(false)
const error = ref('')
const success = ref(false)
const adRequest = ref(null)

// Payment details
const paymentDetails = reactive({
  name: '',
  email: '',
  phone: '',
  cardNumber: '',
  expiryMonth: '',
  expiryYear: '',
  cvv: '',
  amount: 0
})

// Load ad request details
const loadAdRequest = async () => {
  if (!adRequestId.value) return
  
  try {
    loading.value = true
    const response = await sponsorService.getAdRequest(adRequestId.value)
    adRequest.value = response.data
    paymentDetails.amount = adRequest.value.payment_amount
  } catch (err) {
    console.error('Failed to load ad request:', err)
    error.value = 'Failed to load payment details. Please try again.'
  } finally {
    loading.value = false
  }
}

// Format currency
const formatCurrency = (amount) => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0
  }).format(amount || 0)
}

// Process payment
const processPayment = async () => {
  // Validate form first
  if (!validateForm()) return
  
  try {
    processingPayment.value = true
    error.value = ''
    
    // In a real implementation, this would integrate with Razorpay's API
    // For demo purposes, we'll just simulate the payment process
    
    // Simulate API call delay
    await new Promise(resolve => setTimeout(resolve, 2000))
    
    // Create a fake transaction ID
    const transactionId = `rzp_${Date.now()}_${Math.floor(Math.random() * 1000)}`
    
    // Create payment record in our system
    const payload = {
      amount: paymentDetails.amount,
      payment_method: 'Razorpay',
      transaction_id: transactionId
    }
    
    await sponsorService.createPayment(adRequestId.value, payload)
    
    success.value = true
    
  } catch (err) {
    console.error('Payment processing failed:', err)
    error.value = 'Payment processing failed. Please try again.'
  } finally {
    processingPayment.value = false
  }
}

// Validate the payment form
const validateForm = () => {
  // Reset error
  error.value = ''
  
  // Check required fields
  if (!paymentDetails.name.trim()) {
    error.value = 'Please enter your name'
    return false
  }
  
  if (!paymentDetails.email.trim() || !validateEmail(paymentDetails.email)) {
    error.value = 'Please enter a valid email address'
    return false
  }
  
  if (!paymentDetails.phone.trim()) {
    error.value = 'Please enter your phone number'
    return false
  }
  
  // Validate card details
  if (!paymentDetails.cardNumber.trim() || paymentDetails.cardNumber.replace(/\s/g, '').length !== 16) {
    error.value = 'Please enter a valid 16-digit card number'
    return false
  }
  
  if (!paymentDetails.expiryMonth || !paymentDetails.expiryYear) {
    error.value = 'Please enter a valid expiry date'
    return false
  }
  
  if (!paymentDetails.cvv.trim() || paymentDetails.cvv.length !== 3) {
    error.value = 'Please enter a valid 3-digit CVV'
    return false
  }
  
  return true
}

// Validate email format
const validateEmail = (email) => {
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return re.test(email)
}

// Handle card number formatting (add spaces)
const formatCardNumber = (e) => {
  let value = e.target.value.replace(/\s/g, '')
  
  if (value.length > 16) {
    value = value.substring(0, 16)
  }
  
  // Add spaces after every 4 digits
  const formatted = value.replace(/(\d{4})(?=\d)/g, '$1 ')
  paymentDetails.cardNumber = formatted
}

// Return to ad request
const returnToAdRequest = () => {
  router.push(`/sponsor/ad-requests/${adRequestId.value}`)
}

// Load data on mount
onMounted(() => {
  loadAdRequest()
})
</script>

<template>
  <div class="razorpay-payment-view py-5">
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
          
          <!-- Payment success state -->
          <div v-else-if="success" class="card border-0 shadow-sm">
            <div class="card-body text-center p-5">
              <div class="mb-4">
                <div class="success-checkmark">
                  <div class="check-icon">
                    <span class="icon-line line-tip"></span>
                    <span class="icon-line line-long"></span>
                    <div class="icon-circle"></div>
                    <div class="icon-fix"></div>
                  </div>
                </div>
              </div>
              
              <h2 class="mb-3">Payment Successful!</h2>
              <p class="mb-4 text-muted">Your payment of {{ formatCurrency(paymentDetails.amount) }} has been processed successfully.</p>
              
              <button class="btn btn-primary" @click="returnToAdRequest">
                Return to Ad Request
              </button>
            </div>
          </div>
          
          <!-- Payment form -->
          <div v-else class="card border-0 shadow-sm">
            <div class="card-header bg-white border-0 py-3">
              <div class="d-flex justify-content-between align-items-center">
                <h5 class="mb-0">Complete Your Payment</h5>
                <img src="https://razorpay.com/assets/razorpay-logo.svg" alt="Razorpay" height="30" />
              </div>
            </div>
            
            <div class="card-body p-4">
              <!-- Error alert -->
              <div v-if="error" class="alert alert-danger alert-dismissible fade show mb-4">
                {{ error }}
                <button type="button" class="btn-close" @click="error = ''"></button>
              </div>
              
              <!-- Payment summary -->
              <div class="bg-light rounded-3 p-3 mb-4">
                <div class="d-flex justify-content-between align-items-center">
                  <div>
                    <h6 class="mb-1">Payment Amount</h6>
                    <span class="fs-4 fw-bold text-primary">{{ formatCurrency(paymentDetails.amount) }}</span>
                  </div>
                  <div class="text-end">
                    <small class="d-block text-muted mb-1">Ad Request</small>
                    <span>{{ adRequest?.campaign_name }}</span>
                  </div>
                </div>
              </div>
              
              <form @submit.prevent="processPayment">
                <h6 class="mb-3">Personal Information</h6>
                
                <div class="row g-3 mb-4">
                  <div class="col-12">
                    <label for="paymentName" class="form-label">Full Name</label>
                    <input 
                      type="text" 
                      id="paymentName" 
                      class="form-control" 
                      v-model="paymentDetails.name"
                      placeholder="Enter your full name"
                      required
                    />
                  </div>
                  
                  <div class="col-md-6">
                    <label for="paymentEmail" class="form-label">Email Address</label>
                    <input 
                      type="email" 
                      id="paymentEmail" 
                      class="form-control" 
                      v-model="paymentDetails.email"
                      placeholder="you@example.com"
                      required
                    />
                  </div>
                  
                  <div class="col-md-6">
                    <label for="paymentPhone" class="form-label">Phone Number</label>
                    <input 
                      type="tel" 
                      id="paymentPhone" 
                      class="form-control" 
                      v-model="paymentDetails.phone"
                      placeholder="Enter your phone number"
                      required
                    />
                  </div>
                </div>
                
                <h6 class="mb-3">Payment Details</h6>
                
                <div class="row g-3 mb-4">
                  <div class="col-12">
                    <label for="cardNumber" class="form-label">Card Number</label>
                    <div class="input-group">
                      <span class="input-group-text">
                        <i class="bi bi-credit-card"></i>
                      </span>
                      <input 
                        type="text" 
                        id="cardNumber" 
                        class="form-control" 
                        v-model="paymentDetails.cardNumber"
                        @input="formatCardNumber"
                        placeholder="1234 5678 9012 3456"
                        required
                      />
                    </div>
                  </div>
                  
                  <div class="col-md-6">
                    <label class="form-label">Expiry Date</label>
                    <div class="row g-2">
                      <div class="col-6">
                        <select class="form-select" v-model="paymentDetails.expiryMonth" required>
                          <option value="" disabled selected>Month</option>
                          <option v-for="month in 12" :key="month" :value="month < 10 ? `0${month}` : `${month}`">
                            {{ month < 10 ? `0${month}` : month }}
                          </option>
                        </select>
                      </div>
                      <div class="col-6">
                        <select class="form-select" v-model="paymentDetails.expiryYear" required>
                          <option value="" disabled selected>Year</option>
                          <option v-for="year in 10" :key="year" :value="(new Date().getFullYear() + year - 1)">
                            {{ new Date().getFullYear() + year - 1 }}
                          </option>
                        </select>
                      </div>
                    </div>
                  </div>
                  
                  <div class="col-md-6">
                    <label for="cvv" class="form-label">CVV</label>
                    <input 
                      type="password" 
                      id="cvv" 
                      class="form-control" 
                      v-model="paymentDetails.cvv"
                      placeholder="123"
                      maxlength="3"
                      required
                    />
                  </div>
                </div>
                
                <div class="d-grid gap-2 mb-3">
                  <button 
                    type="submit" 
                    class="btn btn-primary btn-lg" 
                    :disabled="processingPayment"
                  >
                    <span v-if="processingPayment" class="spinner-border spinner-border-sm me-2"></span>
                    Proceed to Pay {{ formatCurrency(paymentDetails.amount) }}
                  </button>
                </div>
                
                <div class="text-center">
                  <button type="button" class="btn btn-link" @click="returnToAdRequest">
                    Cancel and return to ad request
                  </button>
                </div>
                
                <div class="mt-4 text-center">
                  <small class="text-muted">Secured by</small>
                  <img src="https://razorpay.com/assets/razorpay-logo.svg" alt="Razorpay" height="20" class="ms-2" />
                </div>
              </form>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.razorpay-payment-view {
  animation: fadeIn 0.5s ease-in-out;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

/* Success checkmark animation */
.success-checkmark {
  width: 80px;
  height: 80px;
  margin: 0 auto;
}

.success-checkmark .check-icon {
  width: 80px;
  height: 80px;
  position: relative;
  border-radius: 50%;
  box-sizing: content-box;
  border: 3px solid #4CAF50;
}

.success-checkmark .check-icon::before {
  content: "";
  position: absolute;
  top: 3px;
  left: -2px;
  width: 30px;
  height: 3px;
  background-color: #4CAF50;
  transform-origin: 100% 100%;
  transform: rotate(-45deg);
  animation: checkmark-before 0.8s ease forwards;
}

.success-checkmark .check-icon::after {
  content: "";
  position: absolute;
  top: 0;
  left: 30px;
  width: 60px;
  height: 3px;
  background-color: #4CAF50;
  transform-origin: 0% 0%;
  transform: rotate(45deg);
  animation: checkmark-after 0.8s ease forwards;
}

@keyframes checkmark-before {
  0% {
    width: 0;
    opacity: 0;
  }
  100% {
    width: 30px;
    opacity: 1;
  }
}

@keyframes checkmark-after {
  0% {
    width: 0;
    opacity: 0;
  }
  100% {
    width: 60px;
    opacity: 1;
  }
}

.check-icon {
  position: relative;
  border-radius: 50%;
  display: block;
  stroke-width: 2;
  stroke: #4CAF50;
  stroke-miterlimit: 10;
  box-shadow: inset 0px 0px 0px #4CAF50;
  animation: fill 0.4s ease-in-out 0.4s forwards, scale 0.3s ease-in-out 0.9s both;
}

.check-icon .icon-circle {
  stroke-dasharray: 166;
  stroke-dashoffset: 166;
  stroke-width: 2;
  stroke-miterlimit: 10;
  stroke: #4CAF50;
  fill: none;
  animation: stroke 0.6s cubic-bezier(0.65, 0, 0.45, 1) forwards;
}

.check-icon .icon-line {
  position: absolute;
  background: #4CAF50;
  border-radius: 10px;
}

.check-icon .icon-line.line-tip {
  top: 46px;
  left: 14px;
  width: 25px;
  height: 3px;
  transform: rotate(45deg);
}

.check-icon .icon-line.line-long {
  top: 38px;
  right: 8px;
  width: 47px;
  height: 3px;
  transform: rotate(-45deg);
}

@keyframes stroke {
  100% {
    stroke-dashoffset: 0;
  }
}

@keyframes fill {
  100% {
    box-shadow: inset 0px 0px 0px 30px #4CAF50;
  }
}

@keyframes scale {
  0%, 100% {
    transform: none;
  }
  50% {
    transform: scale3d(1.1, 1.1, 1);
  }
}
</style> 