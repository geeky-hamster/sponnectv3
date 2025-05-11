<script setup>
import { RouterLink } from 'vue-router'
import { useAuthStore } from '../stores/auth'
//import bg from '../assets/bg.svg'

const authStore = useAuthStore()
</script>

<template>
  <div class="landing-page">
    <!-- Hero Section -->
    <section class="hero text-white py-5">
      <div class="hero-image-container">
        <img 
          src="https://res.cloudinary.com/da9hk6mws/image/upload/v1746987905/videoframe_3455_ry6k3c.png" 
          alt="Sponnect Hero Background" 
          class="hero-background-image"
        />
      </div>
      <div class="container">
        <div class="row align-items-center">
          <div class="col-lg-6">
            <h1 class="display-4 fw-bold mb-4">Connect Brands with Influencers</h1>
            <p class="lead mb-4">
              Sponnect is the premier platform for sponsors and influencers to collaborate on campaigns,
              negotiate deals, and grow together.
            </p>
            <div class="d-flex gap-3">
              <RouterLink v-if="!authStore.isAuthenticated" to="/register" class="btn btn-light btn-lg px-4">Get Started</RouterLink>
              <RouterLink v-else-if="authStore.userRole === 'sponsor'" to="/sponsor/dashboard" class="btn btn-light btn-lg px-4">Dashboard</RouterLink>
              <RouterLink v-else-if="authStore.userRole === 'influencer'" to="/influencer/dashboard" class="btn btn-light btn-lg px-4">Dashboard</RouterLink>
              <RouterLink to="/about" class="btn btn-outline-light btn-lg px-4">Learn More</RouterLink>
            </div>
          </div>
          <div class="col-lg-6 mt-5 mt-lg-0 text-center">
            <img src="../assets/logo.png" alt="Sponnect Platform" class="img-fluid" style="max-height: 400px;">
          </div>
        </div>
      </div>
    </section>

    <!-- Features Section -->
    <section class="features py-5">
      <div class="container">
        <h2 class="text-center mb-5">How Sponnect Works</h2>
        
        <div class="row g-4">
          <div class="col-md-4">
            <div class="card h-100 border-0 shadow-sm">
              <div class="card-body text-center p-4">
                <div class="feature-icon bg-primary text-white mx-auto mb-4">
                  <i class="bi bi-search fs-2"></i>
                </div>
                <h3 class="card-title h5">Discover</h3>
                <p class="card-text">
                  Brands find relevant influencers based on niche, category, and reach.
                  Influencers discover campaigns that match their audience.
                </p>
              </div>
            </div>
          </div>
          
          <div class="col-md-4">
            <div class="card h-100 border-0 shadow-sm">
              <div class="card-body text-center p-4">
                <div class="feature-icon bg-primary text-white mx-auto mb-4">
                  <i class="bi bi-chat-dots fs-2"></i>
                </div>
                <h3 class="card-title h5">Negotiate</h3>
                <p class="card-text">
                  Directly negotiate terms, payments, and campaign requirements
                  through our built-in negotiation system.
                </p>
              </div>
            </div>
          </div>
          
          <div class="col-md-4">
            <div class="card h-100 border-0 shadow-sm">
              <div class="card-body text-center p-4">
                <div class="feature-icon bg-primary text-white mx-auto mb-4">
                  <i class="bi bi-graph-up-arrow fs-2"></i>
                </div>
                <h3 class="card-title h5">Collaborate</h3>
                <p class="card-text">
                  Manage campaigns, track progress, and build lasting relationships
                  for ongoing collaborations.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- User Types Section -->
    <section class="bg-light py-5">
      <div class="container">
        <h2 class="text-center mb-5">Who Uses Sponnect?</h2>
        
        <div class="row g-4">
          <div class="col-md-6">
            <div class="card border-0 shadow-sm">
              <div class="card-body p-4">
                <h3 class="card-title mb-3">
                  <i class="bi bi-briefcase text-primary me-2"></i>
                  Sponsors & Brands
                </h3>
                <ul class="list-group list-group-flush">
                  <li class="list-group-item bg-transparent">Create and manage campaigns</li>
                  <li class="list-group-item bg-transparent">Find relevant influencers by niche and reach</li>
                  <li class="list-group-item bg-transparent">Negotiate terms and payments</li>
                  <li class="list-group-item bg-transparent">Track campaign performance</li>
                </ul>
                <div class="mt-4">
                  <RouterLink v-if="!authStore.isAuthenticated" to="/register" class="btn btn-primary">Register as Sponsor</RouterLink>
                </div>
              </div>
            </div>
          </div>
          
          <div class="col-md-6">
            <div class="card border-0 shadow-sm">
              <div class="card-body p-4">
                <h3 class="card-title mb-3">
                  <i class="bi bi-person-badge text-primary me-2"></i>
                  Influencers & Creators
                </h3>
                <ul class="list-group list-group-flush">
                  <li class="list-group-item bg-transparent">Discover brand partnerships</li>
                  <li class="list-group-item bg-transparent">Apply to relevant campaigns</li>
                  <li class="list-group-item bg-transparent">Negotiate fair compensation</li>
                  <li class="list-group-item bg-transparent">Build long-term brand relationships</li>
                </ul>
                <div class="mt-4">
                  <RouterLink v-if="!authStore.isAuthenticated" to="/register" class="btn btn-primary">Register as Influencer</RouterLink>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Call to Action -->
    <section class="cta py-5 text-white">
      <video 
        class="cta-video" 
        autoplay 
        loop 
        muted 
        playsinline
        src="https://video.wixstatic.com/video/11062b_0a3a288182c34d1294f46fe6a2b17df6/1080p/mp4/file.mp4">
      </video>
      <div class="container text-center">
        <h2 class="mb-4">Ready to get started?</h2>
        <p class="lead mb-4">Join thousands of sponsors and influencers already using Sponnect</p>
        <RouterLink v-if="!authStore.isAuthenticated" to="/register" class="btn btn-light btn-lg px-4 me-2">Sign Up Now</RouterLink>
        <RouterLink v-if="!authStore.isAuthenticated" to="/login" class="btn btn-outline-light btn-lg px-4">Log In</RouterLink>
      </div>
    </section>
  </div>
</template>

<style scoped>
.feature-icon {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.hero {
  position: relative;
  overflow: hidden;
  padding: 80px 0;
  background-color: rgba(0, 0, 0, 0.6);
}

.hero-image-container {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: -1;
}

.hero-background-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.hero .container {
  position: relative;
  z-index: 2;
}

.cta {
  position: relative;
  overflow: hidden;
  padding: 60px 0;
}

.cta::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 1;
}

.cta-video {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  z-index: 0;
}

.cta .container {
  position: relative;
  z-index: 2;
}

</style> 