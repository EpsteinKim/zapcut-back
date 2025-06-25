<template>
	<div class="flex">
		<!-- 모바일 상단 네비게이션 바 (1280px 이하) -->
		<div class="xl:hidden fixed top-0 left-0 right-0 z-50 mobile-nav h-[5vh]">
			<div class="bg-gray-50 border-b border-gray-200">
				<div class="flex items-center justify-between p-3">
					<div class="flex items-center gap-3">
						<Avatar icon="pi pi-video" class="text-purple-600 w-8 h-8" shape="circle" size="small" />
						<div>
							<h2 class="font-semibold text-sm">비디오 편집기</h2>
							<p class="text-xs text-gray-500">{{ currentPageTitle }}</p>
						</div>
					</div>
					<Button :icon="mobileMenuOpen ? 'pi pi-times' : 'pi pi-bars'" variant="text" size="small" class="text-gray-900" @click="toggleMobileMenu" />
				</div>

				<!-- 모바일 드롭다운 메뉴 -->
				<Transition
					enter-active-class="transition-all duration-200 ease-out"
					enter-from-class="opacity-0 -translate-y-2"
					enter-to-class="opacity-100 translate-y-0"
					leave-active-class="transition-all duration-150 ease-in"
					leave-from-class="opacity-100 translate-y-0"
					leave-to-class="opacity-0 -translate-y-2"
				>
					<div v-if="mobileMenuOpen" class="shadow-lg border-t border-purple-300">
						<div class="p-3 space-y-2">
							<NuxtLink
								to="/generate/shorts"
								class="flex items-center gap-3 p-2 rounded-lg hover:bg-purple-50 cursor-pointer transition-all duration-200"
								:class="{ 'bg-purple-50': route.path === '/generate/shorts' }"
								@click="closeMobileMenu"
							>
								<div class="w-6 h-6 bg-purple-100 rounded flex items-center justify-center">
									<i class="pi pi-file-edit text-purple-600 text-xs"></i>
								</div>
								<span class="text-sm font-medium text-gray-900">스크립트 생성</span>
							</NuxtLink>

							<div class="flex items-center gap-3 p-2 rounded-lg opacity-50">
								<div class="w-6 h-6 bg-gray-100 rounded flex items-center justify-center">
									<i class="pi pi-video text-gray-400 text-xs"></i>
								</div>
								<span class="text-sm font-medium text-gray-400">비디오 편집</span>
							</div>
						</div>
					</div>
				</Transition>
			</div>
		</div>

		<!-- 데스크톱 사이드바 (1280px 초과) -->
		<div
			:class="['hidden xl:flex flex-col h-screen fixed border-r border-gray-200 transition-all duration-300', sidebarStore.isCollapsed ? 'w-20' : 'w-80']"
		>
			<LayoutHeader />
			<LayoutMenu />
			<LayoutFooter />
		</div>

		<!-- 메인 콘텐츠 -->
		<main
			:class="[
				'w-full min-h-screen',
				// 모바일/태블릿에서는 상단 패딩, 데스크톱에서는 사이드바 여백
				'pt-16 xl:pt-0',
				'xl:absolute xl:transition-all xl:duration-300 xl:h-screen',
				isDesktop && sidebarStore.isCollapsed
					? 'xl:left-20 xl:w-[calc(100%-5rem)]'
					: isDesktop && !sidebarStore.isCollapsed
						? 'xl:left-80 xl:w-[calc(100%-20rem)]'
						: ''
			]"
		>
			<div class="max-w-screen-2xl mx-auto">
				<slot />
			</div>
		</main>

		<ConfirmDialog />
		<Toast />
		<BlockLoading />
	</div>
</template>

<script setup lang="ts">
	const sidebarStore = useSidebarStore();
	const route = useRoute();
	const mobileMenuOpen = ref(false);
	const isDesktop = ref(false);

	const currentPageTitle = computed(() => {
		if (route.path === '/generate/shorts') {
			return 'YouTube Shorts 생성';
		}
		return 'YouTube Shorts';
	});

	const toggleMobileMenu = () => {
		mobileMenuOpen.value = !mobileMenuOpen.value;
	};

	const closeMobileMenu = () => {
		mobileMenuOpen.value = false;
	};

	const handleResize = (e: MediaQueryListEvent | MediaQueryList) => {
		isDesktop.value = !e.matches;

		if (e.matches) {
			// 1280px 이하: 사이드바 접기, 모바일 메뉴 사용
			sidebarStore.collapse();
		} else {
			// 1280px 초과: 사이드바 펼치기, 모바일 메뉴 닫기
			sidebarStore.sperad();
			mobileMenuOpen.value = false;
		}
	};

	onMounted(() => {
		// 1280px을 기준으로 통일 (xl 브레이크포인트)
		const mediaQuery = window.matchMedia('(max-width: 1280px)');
		mediaQuery.addEventListener('change', handleResize);
		handleResize(mediaQuery);

		// 모바일 메뉴 외부 클릭시 닫기
		document.addEventListener('click', (e) => {
			const target = e.target as HTMLElement;
			if (!target.closest('.mobile-nav') && mobileMenuOpen.value) {
				closeMobileMenu();
			}
		});
	});

	onUnmounted(() => {
		const mediaQuery = window.matchMedia('(max-width: 1280px)');
		mediaQuery.removeEventListener('change', handleResize);
	});
</script>
