<template>
    <section class="py-20 px-4">
        <div class="max-w-screen-lg mx-auto text-center">
            <h2 class="text-3xl md:text-5xl font-bold text-white mb-6">
                몇 번의 클릭으로 바이럴하세요
            </h2>
            <p class="text-xl text-white/80 mb-8 max-w-3xl mx-auto">
                AI로 편집된 매일 숏 비디오를 게시하여 청중을 늘리고 최대 참여를 위해 설계하세요.
                오늘 무료 비디오를 받아보세요.
            </p>
            <Button
label="무료로 시작하기" size="large"
                class="bg-linear-to-r from-purple-500 to-pink-500 text-white px-8 py-3" />
        </div>
    </section>
</template>

<script setup lang="ts">
import { Button } from '#components'
</script>