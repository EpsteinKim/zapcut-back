'use client';

import { Header } from '@/app/components/Header';
import { MainIntroduce } from '@/app/components/MainIntroduce';
import { Features } from '@/app/components/Features';
import { Pricing } from '@/app/components/Pricing';
import { Testimonials } from '@/app/components/Testimonials';
import { FAQ } from '@/app/components/FAQ';
import { CTA } from '@/app/components/CTA';
import { Footer } from '@/app/components/Footer';

export default function RootPage() {
    return (
        <div className="min-h-screen bg-main-gradient">
            <Header />
            <MainIntroduce />
            <Features />
            <Pricing />
            <Testimonials />
            <FAQ />
            <CTA />
            <Footer />
        </div>
    );
}