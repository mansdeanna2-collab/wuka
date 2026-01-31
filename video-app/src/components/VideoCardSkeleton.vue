<template>
  <div class="video-card-skeleton">
    <div class="thumbnail-skeleton skeleton-pulse"></div>
    <div class="info-skeleton">
      <div class="title-skeleton skeleton-pulse"></div>
      <div class="meta-skeleton">
        <div class="category-skeleton skeleton-pulse"></div>
        <div class="count-skeleton skeleton-pulse"></div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'VideoCardSkeleton'
}
</script>

<style scoped>
.video-card-skeleton {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 15px;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.thumbnail-skeleton {
  width: 100%;
  padding-top: 56.25%; /* 16:9 aspect ratio */
  background: linear-gradient(135deg, #2a2a4a 0%, #1a1a3e 100%);
}

.info-skeleton {
  padding: 15px;
}

.title-skeleton {
  height: 18px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
  margin-bottom: 10px;
}

.meta-skeleton {
  display: flex;
  gap: 10px;
}

.category-skeleton {
  width: 60px;
  height: 22px;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 11px;
}

.count-skeleton {
  width: 80px;
  height: 14px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 4px;
}

/* Skeleton pulse animation */
.skeleton-pulse {
  animation: skeleton-pulse 1.5s ease-in-out infinite;
}

@keyframes skeleton-pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

/* Small mobile devices */
@media (max-width: 480px) {
  .video-card-skeleton {
    border-radius: 10px;
  }
  
  .info-skeleton {
    padding: 10px;
  }
  
  .title-skeleton {
    height: 14px;
    margin-bottom: 8px;
  }
  
  .category-skeleton {
    width: 50px;
    height: 18px;
  }
  
  .count-skeleton {
    width: 60px;
    height: 12px;
  }
}
</style>
