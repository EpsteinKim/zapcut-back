<template>
    <header class="sticky top-0 bg-gray-900/90 backdrop-blur-sm shadow-none border-0 z-50">
        <div class="flex justify-between items-center px-6 py-4">
            <h1 class="text-2xl font-bold text-white/90">
                Youtube Short AI
            </h1>
            <nav class="flex items-center space-x-6">
                <a href="#" class="cursor-pointer text-white hover:opacity-80 transition-opacity">
                    기능
                </a>
                <a href="#" class="cursor-pointer text-white hover:opacity-80 transition-opacity">
                    가격
                </a>
                <a href="#" class="cursor-pointer text-white hover:opacity-80 transition-opacity">
                    도구
                </a>
                <Button
label="로그인" outlined
                    class="text-black hover:text-purple-500 hover:opacity-80 transition-opacity" />
            </nav>
        </div>
    </header>
</template>

<script setup lang="ts">
import { Button } from '#components'
</script>