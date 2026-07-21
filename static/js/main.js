document.addEventListener('DOMContentLoaded', () => {
    // State Elements
    const landingState = document.getElementById('landing-state');
    const quizState = document.getElementById('quiz-state');
    const resultsSection = document.getElementById('results-section');
    const loadingOverlay = document.getElementById('loading-overlay');
    const statusUpdate = document.getElementById('status-update');

    // Form & Buttons
    const form = document.getElementById('recommend-form');
    const prevBtn = document.getElementById('prev-btn');
    const nextBtn = document.getElementById('next-btn');
    const submitBtn = document.getElementById('submit-btn');
    const startOverBtn = document.getElementById('start-over-btn');
    const recommendationsContainer = document.getElementById('recommendations-container');

    // Navigation Triggers
    const logoBtn = document.getElementById('logo-btn');
    const navHomeBtns = document.querySelectorAll('.nav-home-btn');
    const startQuizNav = document.getElementById('start-quiz-nav');
    const getStartedBtn = document.getElementById('get-started-btn');
    const ctaQuizBtn = document.getElementById('cta-quiz-btn');
    const browseAllBtn = document.getElementById('browse-all-btn');

    // Quiz Wizard State
    let currentStep = 1;
    const totalSteps = 6;

    // Step Info Configuration
    const stepTitles = {
        1: "Step 1: Choose Your Use Case",
        2: "Step 2: Set Your Performance Level",
        3: "Step 3: Choose Display Size",
        4: "Step 4: Portability Preference",
        5: "Step 5: Brand Preference",
        6: "Step 6: Set Your Budget"
    };

    const stepSubtitles = {
        1: "Select the primary way you'll use your new laptop for the best recommendations in Jordan.",
        2: "Performance level determines processing power and responsiveness of your machine.",
        3: "Screen size dictates both viewing comfort and overall physical dimensions.",
        4: "Portability balances physical weight against maximum cooling capacity and performance.",
        5: "Filter by your preferred brand or select 'Any Brand' for a spec-first search.",
        6: "Set your maximum budget limit to discover the best value deals in Amman."
    };

    // Budget Slider & Input Sync
    const budgetInput = document.getElementById('budget-input');
    const budgetSlider = document.getElementById('budget-slider');

    if (budgetInput && budgetSlider) {
        budgetSlider.addEventListener('input', (e) => {
            budgetInput.value = e.target.value;
        });
        budgetInput.addEventListener('input', (e) => {
            let val = parseInt(e.target.value, 10);
            if (isNaN(val)) val = 100;
            if (val > 10000) val = 10000;
            budgetSlider.value = Math.min(val, 3000); // Slider visual limit is 3000
        });
    }

    // Toggle Pages/States
    function showLanding() {
        landingState.classList.remove('hidden');
        quizState.classList.add('hidden');
        resultsSection.classList.add('hidden');
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    function startQuiz() {
        landingState.classList.add('hidden');
        resultsSection.classList.add('hidden');
        quizState.classList.remove('hidden');
        currentStep = 1;
        updateWizard();
    }

    // Event Listeners for Nav
    if (logoBtn) logoBtn.addEventListener('click', showLanding);
    navHomeBtns.forEach(btn => btn.addEventListener('click', showLanding));
    if (startQuizNav) startQuizNav.addEventListener('click', startQuiz);
    if (getStartedBtn) getStartedBtn.addEventListener('click', startQuiz);
    if (ctaQuizBtn) ctaQuizBtn.addEventListener('click', startQuiz);
    
    if (browseAllBtn) {
        browseAllBtn.addEventListener('click', async () => {
            // Bypass quiz and fetch all/top laptops
            showLoading(true);
            try {
                const response = await fetch('/api/laptops');
                const result = await response.json();
                displayRecommendations(result.laptops || []);
            } catch (error) {
                console.error("Error loading laptops:", error);
            } finally {
                showLoading(false);
            }
        });
    }

    // Wizard Update Logic
    function updateWizard() {
        // Step titles & subtitles
        document.getElementById('quiz-step-title').textContent = stepTitles[currentStep];
        document.getElementById('quiz-step-subtitle').textContent = stepSubtitles[currentStep];

        // Step numbers
        document.getElementById('wizard-step-indicator').textContent = `Step ${currentStep} of ${totalSteps}`;

        // Visibility of panels
        document.querySelectorAll('.quiz-step-section').forEach(section => {
            const stepIndex = parseInt(section.getAttribute('data-step-content'), 10);
            if (stepIndex === currentStep) {
                section.classList.remove('hidden');
                section.classList.add('active');
            } else {
                section.classList.add('hidden');
                section.classList.remove('active');
            }
        });

        // Sidebar indicators
        document.querySelectorAll('.sidebar-step-item').forEach(item => {
            const stepNavIndex = parseInt(item.getAttribute('data-step-nav'), 10);
            if (stepNavIndex === currentStep) {
                item.className = "sidebar-step-item flex items-center gap-3 px-4 py-3 rounded-xl border border-electric-blue/30 bg-electric-blue/10 text-on-surface shadow-[0_0_15px_rgba(59,130,246,0.1)]";
            } else if (stepNavIndex < currentStep) {
                item.className = "sidebar-step-item flex items-center gap-3 px-4 py-3 rounded-xl border border-jod-green/20 bg-jod-green/5 text-jod-green";
            } else {
                item.className = "sidebar-step-item flex items-center gap-3 px-4 py-3 rounded-xl border border-white/5 text-outline hover:bg-white/5";
            }
        });

        // Prev Button States
        if (currentStep === 1) {
            prevBtn.classList.add('opacity-50', 'pointer-events-none');
        } else {
            prevBtn.classList.remove('opacity-50', 'pointer-events-none');
        }

        // Submit/Next Button States
        if (currentStep === totalSteps) {
            nextBtn.classList.add('hidden');
            submitBtn.classList.remove('hidden');
        } else {
            nextBtn.classList.remove('hidden');
            submitBtn.classList.add('hidden');
        }

        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    // Step Nav Button Handlers
    nextBtn.addEventListener('click', (e) => {
        e.preventDefault();
        if (currentStep < totalSteps) {
            currentStep++;
            updateWizard();
        }
    });

    prevBtn.addEventListener('click', (e) => {
        e.preventDefault();
        if (currentStep > 1) {
            currentStep--;
            updateWizard();
        }
    });

    // Form Submission
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        showLoading(true);

        const payload = {
            use_case: document.querySelector('input[name="use_case"]:checked').value,
            performance: document.querySelector('input[name="performance"]:checked').value,
            screen_size: document.querySelector('input[name="screen_size"]:checked').value,
            portability: document.querySelector('input[name="portability"]:checked').value,
            brand: document.querySelector('input[name="brand"]:checked').value,
            budget: parseInt(budgetInput.value, 10)
        };

        // Delay for simulated analysis
        setTimeout(async () => {
            try {
                const response = await fetch('/api/recommend', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const result = await response.json();
                displayRecommendations(result.recommendations || []);
            } catch (error) {
                console.error('Error fetching recommendations:', error);
            } finally {
                showLoading(false);
            }
        }, 2500);
    });

    // Start Over
    startOverBtn.addEventListener('click', () => {
        showLanding();
    });

    // Loading overlay handling
    let statusInterval;
    const statuses = [
        "Scanning Amman retail stocks...",
        "Analyzing hardware benchmarks...",
        "Comparing price histories...",
        "Optimizing performance-to-price ratios...",
        "Stitching recommendation cards..."
    ];

    function showLoading(show) {
        if (show) {
            loadingOverlay.classList.remove('hidden');
            let i = 0;
            statusUpdate.textContent = statuses[0];
            statusInterval = setInterval(() => {
                i = (i + 1) % statuses.length;
                statusUpdate.textContent = statuses[i];
            }, 1200);
        } else {
            loadingOverlay.classList.add('hidden');
            clearInterval(statusInterval);
        }
    }

    // Recommendation Rendering
    function displayRecommendations(laptops) {
        recommendationsContainer.innerHTML = '';
        
        if (!laptops || laptops.length === 0) {
            recommendationsContainer.innerHTML = `
                <div class="col-span-full text-center py-12 glass-card rounded-2xl border-white/5">
                    <span class="material-symbols-outlined text-[64px] text-outline mb-4">search_off</span>
                    <h3 class="font-headline-md text-headline-md text-on-surface mb-2">No Laptops Found</h3>
                    <p class="font-body-md text-body-md text-on-surface-variant max-w-md mx-auto">
                        We couldn't find any matching laptops within your budget range. Try starting over with a higher budget limit.
                    </p>
                </div>
            `;
        } else {
            laptops.forEach((laptop, index) => {
                const card = createRecommendationCard(laptop, index);
                recommendationsContainer.appendChild(card);
            });
        }

        quizState.classList.add('hidden');
        landingState.classList.add('hidden');
        resultsSection.classList.remove('hidden');
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    function createRecommendationCard(laptop, index) {
        const isTop = index === 0;
        const matchScore = laptop.match_score || (98 - index * 3);
        const imageUrl = laptop.image_url || 'https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=500&q=80';
        
        const card = document.createElement('div');
        card.className = `relative glass-card rounded-2xl p-6 flex flex-col justify-between border-white/10 hover:border-electric-blue/30 transition-all duration-300 shadow-xl ${
            isTop ? 'ring-2 ring-electric-blue/40 shadow-electric-blue/5' : ''
        }`;

        // Build retail offers HTML
        let offersHtml = '';
        if (laptop.shop_offers && laptop.shop_offers.length > 0) {
            offersHtml = `
                <div class="mt-4 pt-4 border-t border-white/5">
                    <span class="text-[11px] font-bold text-outline uppercase tracking-wider block mb-2">Available At Local Stores</span>
                    <div class="flex flex-col gap-2">
                        ${laptop.shop_offers.map(offer => `
                            <div class="flex justify-between items-center bg-surface-container-lowest p-2 rounded-lg border border-white/5 hover:border-white/10 transition-colors">
                                <span class="font-label-sm text-[13px] text-on-surface-variant font-medium">${offer.shop_name}</span>
                                <div class="flex items-center gap-3">
                                    <span class="font-bold text-jod-green text-[14px]">${offer.price_jod} JOD</span>
                                    ${offer.product_url ? `
                                        <a href="${offer.product_url}" target="_blank" class="px-3 py-1 bg-electric-blue text-white rounded text-[11px] font-bold hover:bg-blue-600 transition-colors inline-flex items-center gap-1">
                                            Go to Shop
                                            <span class="material-symbols-outlined text-[10px]">open_in_new</span>
                                        </a>
                                    ` : ''}
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        } else {
            offersHtml = `
                <div class="mt-4 pt-4 border-t border-white/5 text-center text-outline text-[13px]">
                    Price details not available. Contact retailers directly.
                </div>
            `;
        }

        card.innerHTML = `
            <div>
                ${isTop ? `
                    <div class="absolute -top-3 left-6 px-4 py-1 rounded-full bg-gradient-to-r from-electric-blue to-blue-600 text-white font-bold text-[11px] uppercase tracking-wider shadow-lg shadow-blue-500/20">
                        Top Recommendation
                    </div>
                ` : ''}
                
                <div class="w-full h-44 bg-surface-container rounded-xl overflow-hidden flex items-center justify-center relative mb-6 border border-white/5">
                    <img src="${imageUrl}" alt="${laptop.model}" class="object-contain max-h-36 max-w-full hover:scale-105 transition-transform duration-300" onerror="this.src='https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=500&q=80'">
                </div>

                <div class="flex justify-between items-start mb-4">
                    <div>
                        <h3 class="font-headline-md text-headline-md text-on-surface leading-tight">${laptop.brand} ${laptop.model}</h3>
                        <span class="text-[12px] text-outline font-bold uppercase tracking-wider block mt-1">JOD ${laptop.price_jod}</span>
                    </div>
                    <div class="flex flex-col items-center justify-center bg-electric-blue/15 text-electric-blue rounded-full w-14 h-14 border border-electric-blue/30 shrink-0">
                        <span class="font-bold text-[16px]">${matchScore}%</span>
                        <span class="text-[9px] uppercase font-bold tracking-widest text-outline -mt-1">Match</span>
                    </div>
                </div>

                <!-- Spec List -->
                <div class="grid grid-cols-2 gap-x-4 gap-y-2 mb-6 bg-surface-container-low p-4 rounded-xl border border-white/5">
                    <div class="flex items-center gap-2 text-on-surface-variant text-[13px]">
                        <span class="material-symbols-outlined text-[18px] text-outline">memory</span>
                        <span class="truncate">${laptop.cpu || 'Intel / AMD CPU'}</span>
                    </div>
                    <div class="flex items-center gap-2 text-on-surface-variant text-[13px]">
                        <span class="material-symbols-outlined text-[18px] text-outline">developer_board</span>
                        <span class="truncate">${laptop.gpu || 'Integrated GPU'}</span>
                    </div>
                    <div class="flex items-center gap-2 text-on-surface-variant text-[13px]">
                        <span class="material-symbols-outlined text-[18px] text-outline">ram</span>
                        <span>${laptop.ram || '8GB RAM'}</span>
                    </div>
                    <div class="flex items-center gap-2 text-on-surface-variant text-[13px]">
                        <span class="material-symbols-outlined text-[18px] text-outline">hard_drive</span>
                        <span>${laptop.storage || '256GB'} ${laptop.storage_type || 'SSD'}</span>
                    </div>
                    <div class="flex items-center gap-2 text-on-surface-variant text-[13px] col-span-2">
                        <span class="material-symbols-outlined text-[18px] text-outline">aspect_ratio</span>
                        <span>${laptop.screen_size ? laptop.screen_size + '"' : '15.6"'} Screen</span>
                    </div>
                </div>

                <!-- AI reasoning -->
                <div class="bg-surface-container-highest/30 border border-white/5 rounded-xl p-4 mb-4">
                    <div class="flex items-center gap-2 font-bold text-headline-sm text-electric-blue text-[13px] mb-2">
                        <span class="material-symbols-outlined text-[16px]">sparkles</span>
                        AI Reasoning
                    </div>
                    <p class="font-body-md text-[13px] text-on-surface-variant leading-relaxed">
                        ${laptop.reasoning || 'Matches your required specifications and budget nicely. High reliability rating in Amman local marketplace.'}
                    </p>
                </div>
            </div>

            <!-- Shop Offers list -->
            ${offersHtml}
        `;
        
        return card;
    }
});
