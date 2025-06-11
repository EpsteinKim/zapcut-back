<template>
    <div class="min-h-screen bg-linear-to-br from-gray-900 via-purple-900 to-blue-950">
        <AppHeader />
        <AppMainIntroduce />
        <AppFeatures />
        <AppPricing />
        <AppTestimonials />
        <AppFAQ />
        <AppCTA />
        <AppFooter />
    </div>
</template>

<script setup lang="ts">

definePageMeta({
    layout: 'none',
})
useHead({
    title: 'Youtube Shorts AI',
    meta: [
        { name: 'description', content: 'AI로 자동 생성하는 YouTube Shorts' }
    ]
})
</script>