document.addEventListener('DOMContentLoaded', () => {
    const resultsContainer = document.getElementById('results-container');
    const loadingSpinner = document.getElementById('loading-spinner');
    const startOverBar = document.getElementById('start-over-bar');

    // Retrieve recommendation data from sessionStorage
    const savedResults = sessionStorage.getItem('quiz_results');
    const savedQuizData = sessionStorage.getItem('quiz_data');

    let recommendations = [];
    let quizData = null;

    if (savedResults) {
        try {
            recommendations = JSON.parse(savedResults);
        } catch (e) {
            console.error("Error parsing results:", e);
        }
    }

    if (savedQuizData) {
        try {
            quizData = JSON.parse(savedQuizData);
        } catch (e) {
            console.error("Error parsing quiz data:", e);
        }
    }

    // Hide spinner
    if (loadingSpinner) loadingSpinner.classList.add('hidden');

    // Render filter summary if quiz data exists
    if (quizData && resultsContainer) {
        const summaryBar = document.createElement('div');
        summaryBar.className = "flex flex-wrap gap-2 items-center p-4 glass-panel rounded-xl mb-6 border border-white/10 text-sm";
        summaryBar.innerHTML = `
            <span class="font-bold text-electric-blue flex items-center gap-1">
                <span class="material-symbols-outlined text-[18px]">tune</span> Search Signals:
            </span>
            <span class="bg-white/10 px-3 py-1 rounded-full text-on-surface font-medium">Budget: ≤ ${quizData.budget || 1500} JOD</span>
            <span class="bg-white/10 px-3 py-1 rounded-full text-on-surface font-medium capitalize">Use: ${quizData.use_case || 'General'}</span>
            <span class="bg-white/10 px-3 py-1 rounded-full text-on-surface font-medium capitalize">Perf: ${quizData.performance || 'Medium'}</span>
            <span class="bg-white/10 px-3 py-1 rounded-full text-on-surface font-medium">Display: ${quizData.screen_size || '15-16'}"</span>
            <span class="bg-white/10 px-3 py-1 rounded-full text-on-surface font-medium">Brand: ${quizData.brand || 'Any'}</span>
        `;
        resultsContainer.before(summaryBar);
    }

    if (!recommendations || recommendations.length === 0) {
        if (resultsContainer) {
            resultsContainer.classList.remove('hidden');
            resultsContainer.innerHTML = `
                <div class="text-center py-16 p-8 glass-panel rounded-2xl border border-white/10">
                    <span class="material-symbols-outlined text-[64px] text-electric-blue mb-4">search_off</span>
                    <h3 class="font-headline-lg text-headline-lg text-on-surface mb-2">No Matching Laptops Found</h3>
                    <p class="font-body-lg text-body-lg text-on-surface-variant max-w-lg mx-auto mb-6">
                        We couldn't find laptops matching all your criteria within your specified budget. Try adjusting your budget slider or brand preference.
                    </p>
                    <a href="/quiz" class="inline-flex items-center gap-2 px-8 py-3 bg-electric-blue text-white rounded-xl font-bold hover:bg-primary-container transition-all">
                        <span class="material-symbols-outlined">restart_alt</span> Try Searching Again
                    </a>
                </div>
            `;
        }
        return;
    }

    if (resultsContainer) {
        resultsContainer.classList.remove('hidden');
    }
    if (startOverBar) {
        startOverBar.classList.remove('hidden');
    }

    // Render recommendation cards
    recommendations.forEach((laptop, index) => {
        const laptopCard = createLaptopCard(laptop, index);
        resultsContainer.appendChild(laptopCard);
    });

    function formatRam(ram) {
        if (!ram) return '8GB RAM';
        if (typeof ram === 'string' && ram.toLowerCase().includes('gb')) return ram;
        return `${ram}GB RAM`;
    }

    function formatStorage(size, type) {
        if (!size) return '256GB SSD';
        const stType = type || 'SSD';
        if (typeof size === 'number') {
            if (size >= 1024) return `${size / 1024}TB ${stType}`;
            return `${size}GB ${stType}`;
        }
        return `${size} ${stType}`;
    }

    function createLaptopCard(laptop, index) {
        const section = document.createElement('section');
        section.className = `fade-in grid grid-cols-1 lg:grid-cols-12 gap-6 p-6 md:p-8 rounded-2xl glass-panel border border-white/10 shadow-2xl hover:border-electric-blue/30 transition-all`;
        section.style.animationDelay = `${index * 0.1}s`;

        const matchScore = laptop.match_score || Math.max(65, 98 - index * 4);
        const imageUrl = laptop.image_url || 'https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=500&q=80';
        const offers = laptop.shop_offers || [];

        const rankLabels = {
            0: { label: 'Top Recommendation', color: 'bg-electric-blue/20 text-electric-blue border-electric-blue/40' },
            1: { label: 'Great Value Choice', color: 'bg-jod-green/20 text-jod-green border-jod-green/40' },
            2: { label: 'Alternative Pick', color: 'bg-white/10 text-on-surface border-white/20' }
        };

        const rankInfo = rankLabels[index] || { label: `Rank #${index + 1}`, color: 'bg-white/10 text-on-surface border-white/20' };

        section.innerHTML = `
            <!-- Left: Image & Badges -->
            <div class="lg:col-span-5 flex flex-col items-center justify-between bg-surface-container-low rounded-xl p-6 border border-white/5 relative min-h-[260px]">
                <div class="w-full flex justify-between items-center mb-4">
                    <span class="px-3 py-1 rounded-full text-xs font-bold border ${rankInfo.color}">
                        ${rankInfo.label}
                    </span>
                    <div class="flex items-center gap-1.5 px-3 py-1 rounded-full bg-electric-blue/15 border border-electric-blue/30 text-electric-blue">
                        <span class="material-symbols-outlined text-[16px]">bolt</span>
                        <span class="font-bold text-sm">${matchScore}% Match</span>
                    </div>
                </div>

                <div class="w-full flex-grow flex items-center justify-center p-4">
                    <img class="max-h-48 w-auto object-contain transform hover:scale-105 transition-transform duration-500" 
                         src="${imageUrl}" 
                         alt="${laptop.brand} ${laptop.model}"
                         onerror="this.src='https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=500&q=80'">
                </div>
            </div>

            <!-- Right: Specs, Reasoning & Deals -->
            <div class="lg:col-span-7 flex flex-col justify-between">
                <div>
                    <!-- Header & Price -->
                    <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 mb-3">
                        <div>
                            <span class="text-xs font-bold uppercase tracking-wider text-electric-blue">${laptop.brand}</span>
                            <h2 class="font-headline-lg text-xl md:text-2xl text-on-surface font-bold leading-tight">${laptop.model}</h2>
                        </div>
                        <div class="text-left sm:text-right">
                            <span class="text-xs text-on-surface-variant block">Best Retail Price</span>
                            <span class="font-display-lg text-2xl md:text-3xl text-jod-green font-bold">${laptop.price_jod} <span class="text-base font-medium">JOD</span></span>
                        </div>
                    </div>

                    <!-- Specs Badges -->
                    <div class="flex flex-wrap gap-2 mb-4">
                        <div class="flex items-center gap-1.5 px-3 py-1.5 bg-surface-container rounded-lg border border-white/5 text-xs text-on-surface">
                            <span class="material-symbols-outlined text-[16px] text-electric-blue">memory</span>
                            <span>${laptop.cpu || 'Processor'}</span>
                        </div>
                        <div class="flex items-center gap-1.5 px-3 py-1.5 bg-surface-container rounded-lg border border-white/5 text-xs text-on-surface">
                            <span class="material-symbols-outlined text-[16px] text-electric-blue">developer_board</span>
                            <span>${laptop.gpu || 'Graphics'}</span>
                        </div>
                        <div class="flex items-center gap-1.5 px-3 py-1.5 bg-surface-container rounded-lg border border-white/5 text-xs text-on-surface">
                            <span class="material-symbols-outlined text-[16px] text-electric-blue">ram</span>
                            <span>${formatRam(laptop.ram)}</span>
                        </div>
                        <div class="flex items-center gap-1.5 px-3 py-1.5 bg-surface-container rounded-lg border border-white/5 text-xs text-on-surface">
                            <span class="material-symbols-outlined text-[16px] text-electric-blue">hard_drive</span>
                            <span>${formatStorage(laptop.storage, laptop.storage_type)}</span>
                        </div>
                        <div class="flex items-center gap-1.5 px-3 py-1.5 bg-surface-container rounded-lg border border-white/5 text-xs text-on-surface">
                            <span class="material-symbols-outlined text-[16px] text-electric-blue">aspect_ratio</span>
                            <span>${laptop.screen_size ? laptop.screen_size + '" Screen' : '15.6" Screen'}</span>
                        </div>
                    </div>

                    <!-- Why Picked / AI Reasoning Box -->
                    <div class="bg-electric-blue/10 border border-electric-blue/20 rounded-xl p-4 mb-4">
                        <div class="flex items-center gap-2 font-bold text-electric-blue text-xs uppercase tracking-wider mb-1">
                            <span class="material-symbols-outlined text-[16px]">auto_awesome</span>
                            Why This Laptop Was Picked For You
                        </div>
                        <p class="text-on-surface text-sm leading-relaxed">
                            ${laptop.reasoning || 'Matches your required specifications and budget nicely based on local retail availability in Amman.'}
                        </p>
                    </div>
                </div>

                <!-- Retail Store Offers -->
                <div class="mt-2 pt-4 border-t border-white/10">
                    <span class="text-xs font-bold text-on-surface-variant uppercase tracking-wider block mb-3">Available In Amman Stores</span>
                    <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                        ${offers.length > 0 ? offers.map(offer => `
                            <div class="p-3 rounded-xl bg-white/5 border border-white/10 flex justify-between items-center hover:border-electric-blue/40 transition-colors">
                                <div>
                                    <p class="font-semibold text-on-surface text-sm">${offer.shop_name}</p>
                                    <p class="text-jod-green font-bold text-sm">${offer.price_jod} JOD</p>
                                </div>
                                ${offer.product_url ? `
                                    <a href="${offer.product_url}" target="_blank" rel="noopener" class="px-3 py-1.5 bg-electric-blue text-white rounded-lg text-xs font-bold hover:bg-primary-container transition-all flex items-center gap-1">
                                        View Deal <span class="material-symbols-outlined text-[14px]">open_in_new</span>
                                    </a>
                                ` : '<span class="text-xs text-on-surface-variant">In Stock</span>'}
                            </div>
                        `).join('') : `
                            <div class="p-3 rounded-xl bg-white/5 border border-white/10 col-span-2 text-center text-on-surface-variant text-xs italic">
                                Local retail stock available in Amman stores. Contact local suppliers for current availability.
                            </div>
                        `}
                    </div>
                </div>
            </div>
        `;

        return section;
    }
});
