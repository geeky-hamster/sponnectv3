<tr v-for="campaign in campaigns" :key="campaign.id" 
    :class="{ 'table-info': campaign.is_featured, 'table-danger': campaign.is_flagged }">
  <td>
    <div class="fw-semibold text-truncate" style="max-width: 200px;">
      {{ campaign.title || campaign.name }}
      <i v-if="campaign.is_featured" class="bi bi-star-fill text-warning ms-2" title="Featured"></i>
      <i v-if="campaign.is_flagged" class="bi bi-flag-fill text-danger ms-2" title="Flagged"></i>
    </div>
    <small class="text-muted">ID: {{ campaign.id }}</small>
  </td>
  <td>
    <button class="btn btn-secondary dropdown-toggle" type="button" data-bs-toggle="dropdown" aria-expanded="false">
      Actions
    </button>
    <ul class="dropdown-menu">
      <li>
        <button class="dropdown-item" @click="viewCampaignDetails(campaign)">
          <i class="bi bi-eye me-2"></i>View Details
        </button>
      </li>
      
      <!-- Status actions -->
      <li v-if="campaign.status === 'pending_approval'">
        <button class="dropdown-item" @click="showConfirmation('approve', campaign)">
          <i class="bi bi-check-circle text-success me-2"></i>Approve
        </button>
        <button class="dropdown-item" @click="showConfirmation('reject', campaign)">
          <i class="bi bi-x-circle text-danger me-2"></i>Reject
        </button>
      </li>
      
      <li v-if="campaign.status === 'active'">
        <button class="dropdown-item" @click="showConfirmation('pause', campaign)">
          <i class="bi bi-pause-circle text-warning me-2"></i>Pause
        </button>
      </li>
      
      <li v-if="campaign.status === 'paused' || campaign.status === 'rejected'">
        <button class="dropdown-item" @click="showConfirmation('activate', campaign)">
          <i class="bi bi-play-circle text-success me-2"></i>Activate
        </button>
      </li>
      
      <!-- Flag/Unflag actions -->
      <li v-if="!campaign.is_flagged">
        <button class="dropdown-item" @click="showConfirmation('flag', campaign)">
          <i class="bi bi-flag-fill text-danger me-2"></i>Flag Campaign
        </button>
      </li>
      <li v-else>
        <button class="dropdown-item" @click="showConfirmation('unflag', campaign)">
          <i class="bi bi-flag text-success me-2"></i>Unflag Campaign
        </button>
      </li>
    </ul>
  </td>
</tr>

const getActionTitle = (action) => {
  switch (action) {
    case 'approve': return 'Approve Campaign'
    case 'reject': return 'Reject Campaign'
    case 'pause': return 'Pause Campaign'
    case 'activate': return 'Activate Campaign'
    case 'feature': return 'Feature Campaign'
    case 'unfeature': return 'Unfeature Campaign'
    case 'flag': return 'Flag Campaign'
    case 'unflag': return 'Unflag Campaign'
    default: return 'Confirm Action'
  }
}

const getActionMessage = (action, campaign) => {
  switch (action) {
    case 'approve': 
      return `Are you sure you want to approve the campaign "${campaign.title || campaign.name}"? This will make it visible to influencers.`
    case 'reject': 
      return `Are you sure you want to reject the campaign "${campaign.title || campaign.name}"? The sponsor will be notified.`
    case 'pause': 
      return `Are you sure you want to pause the campaign "${campaign.title || campaign.name}"? This will temporarily hide it from influencers.`
    case 'activate': 
      return `Are you sure you want to activate the campaign "${campaign.title || campaign.name}"? This will make it visible to influencers.`
    case 'feature': 
      return `Are you sure you want to feature the campaign "${campaign.title || campaign.name}"? This will show it prominently to influencers.`
    case 'unfeature': 
      return `Are you sure you want to remove the featured status from "${campaign.title || campaign.name}"?`
    case 'flag':
      return `Are you sure you want to flag the campaign "${campaign.title || campaign.name}"? This will hide it from non-admin users and restrict interactions.`
    case 'unflag':
      return `Are you sure you want to unflag the campaign "${campaign.title || campaign.name}"? This will make it visible again according to its status.`
    default: 
      return 'Are you sure you want to perform this action?'
  }
}

switch (type) {
  case 'approve':
    await adminService.approveCampaign(campaign.id)
    success.value = `Campaign "${campaign.title || campaign.name}" has been approved`
    break
  case 'reject':
    await adminService.rejectCampaign(campaign.id)
    success.value = `Campaign "${campaign.title || campaign.name}" has been rejected`
    break
  case 'pause':
    await adminService.pauseCampaign(campaign.id)
    success.value = `Campaign "${campaign.title || campaign.name}" has been paused`
    break
  case 'activate':
    await adminService.activateCampaign(campaign.id)
    success.value = `Campaign "${campaign.title || campaign.name}" has been activated`
    break
  case 'feature':
    await adminService.featureCampaign(campaign.id)
    success.value = `Campaign "${campaign.title || campaign.name}" has been featured`
    break
  case 'unfeature':
    await adminService.unfeatureCampaign(campaign.id)
    success.value = `Campaign "${campaign.title || campaign.name}" has been unfeatured`
    break
  case 'flag':
    await adminService.flagCampaign(campaign.id)
    success.value = `Campaign "${campaign.title || campaign.name}" has been flagged`
    break
  case 'unflag':
    await adminService.unflagCampaign(campaign.id)
    success.value = `Campaign "${campaign.title || campaign.name}" has been unflagged`
    break
} 