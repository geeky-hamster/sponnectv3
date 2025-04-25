<template>
  <!-- No changes to template section -->
</template>

<script>
import { influencerService, sponsorService } from '../services/services';

export default {
  // No changes to component options
};
</script>

<script>
export default {
  methods: {
    async handleSubmit() {
      this.submitting = true;
      this.submissionError = null;

      try {
        // Build the payload with the correct action field
        const payload = {
          action: this.responseForm.status, // Use status as the action
          message: this.responseForm.message || ''
        };

        // If negotiating, include the payment amount
        if (this.responseForm.status === 'negotiate') {
          payload.payment_amount = parseFloat(this.responseForm.payment_amount || 0);
        }

        console.log('Submitting response with payload:', payload);

        if (this.userRole === 'influencer') {
          // Use the updated influencer service
          await influencerService.respondToAdRequest(this.adRequestId, payload);
        } else if (this.userRole === 'sponsor') {
          await sponsorService.respondToAdRequest(this.adRequestId, payload);
        }

        // Reset form and reload data after successful submission
        this.resetForm();
        await this.loadAdRequest();
        
        this.$toast.success('Response submitted successfully');
      } catch (error) {
        console.error('Error submitting response:', error);
        
        // Enhanced error handling to show specific errors from the server
        if (error.response?.data?.message) {
          this.submissionError = error.response.data.message;
        } else if (error.response?.data?.error) {
          this.submissionError = error.response.data.error;
        } else {
          this.submissionError = 'Failed to submit response. Please try again.';
        }
        
        this.$toast.error(this.submissionError);
      } finally {
        this.submitting = false;
      }
    },
  },
};
</script> 