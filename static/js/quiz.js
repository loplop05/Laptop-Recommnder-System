document.addEventListener('DOMContentLoaded', () => {
    // Elements
    const form = document.getElementById('recommend-form');
    const prevBtn = document.getElementById('prev-btn');
    const nextBtn = document.getElementById('next-btn');
    const progressEl = document.getElementById('quiz-progress-bar');
    const indicatorEl = document.getElementById('quiz-step-indicator');
    const titleEl = document.getElementById('quiz-step-title');
    const subtitleEl = document.getElementById('quiz-step-subtitle');
    const loadingOverlay = document.getElementById('loading-overlay');
    const statusUpdate = document.getElementById('status-update');

    // Budget range and display syncing
    const budgetInput = document.getElementById('budget-input');
    const budgetSlider = document.getElementById('budget-slider');
    const budgetDisplayVal = document.getElementById('budget-display-val');

    if (budgetSlider && budgetDisplayVal && budgetInput) {
        budgetSlider.addEventListener('input', (e) => {
            const val = e.target.value;
            budgetDisplayVal.textContent = val;
            budgetInput.value = val;
        });
    }

    // Wizard step state
    let currentStep = 1;
    const totalSteps = 7;

    const stepTitles = {
        1: "What's your primary use?",
        2: "What's your maximum budget?",
        3: "What's your ideal display size?",
        4: "How important is mobility?",
        5: "How much performance power do you need?",
        6: "Do you have an OS preference?",
        7: "Any specific brand preference?"
    };

    const stepSubtitles = {
        1: "Select how you will primarily use your new laptop.",
        2: "Adjust the slider to set your spending limit in JOD.",
        3: "Choose screen dimensions for work & viewing comfort.",
        4: "Balance weight & portability against desktop performance.",
        5: "Choose the CPU & GPU performance level required.",
        6: "Filter by operating system preference (Windows, macOS, or No Preference).",
        7: "Filter by your preferred brand or select 'Any Brand' for a spec-first search."
    };

    function updateWizard() {
        // Update Title & Subtitle
        if (titleEl) titleEl.textContent = stepTitles[currentStep] || "";
        if (subtitleEl) subtitleEl.textContent = stepSubtitles[currentStep] || "";

        // Toggle sections visibility
        document.querySelectorAll('.quiz-step-section').forEach(section => {
            const step = parseInt(section.getAttribute('data-step-content'), 10);
            if (step === currentStep) {
                section.classList.remove('hidden');
                section.classList.add('active');
            } else {
                section.classList.add('hidden');
                section.classList.remove('active');
            }
        });

        // Update progress bar
        const pct = (currentStep / totalSteps) * 100;
        if (progressEl) progressEl.style.width = `${pct}%`;
        if (indicatorEl) indicatorEl.textContent = `Step ${currentStep} of ${totalSteps}`;

        // Previous button opacity and clickability
        if (currentStep === 1) {
            prevBtn.classList.add('opacity-0', 'pointer-events-none');
        } else {
            prevBtn.classList.remove('opacity-0', 'pointer-events-none');
        }

        // Change button text on final step
        if (currentStep === totalSteps) {
            nextBtn.innerHTML = `Show Recommendations <span class="material-symbols-outlined text-[18px]">search</span>`;
            nextBtn.className = "bg-jod-green text-white px-8 py-3 rounded-lg font-bold hover:brightness-110 active:scale-95 transition-all flex items-center gap-2 cursor-pointer";
        } else {
            nextBtn.innerHTML = `Next Step <span class="material-symbols-outlined text-[18px]">arrow_forward</span>`;
            nextBtn.className = "bg-electric-blue text-white px-8 py-3 rounded-lg font-bold hover:brightness-110 active:scale-95 transition-all flex items-center gap-2 cursor-pointer";
        }

        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    // Initial setup
    updateWizard();

    // Helper for safe radio extraction
    function getSelectedValue(name, fallback = '') {
        const checked = document.querySelector(`input[name="${name}"]:checked`);
        return checked ? checked.value : fallback;
    }

    // Event Handlers
    nextBtn.addEventListener('click', (e) => {
        e.preventDefault();

        if (currentStep < totalSteps) {
            currentStep++;
            updateWizard();
        } else {
            let brandVal = getSelectedValue('brand', 'Any');
            const osPref = getSelectedValue('os_pref', 'any');
            
            // Map OS preference if user chose macOS and Any brand
            if (osPref === 'macos' && brandVal === 'Any') {
                brandVal = 'Apple';
            }

            const payload = {
                use_case: getSelectedValue('use_case', 'general'),
                performance: getSelectedValue('performance', 'medium'),
                screen_size: getSelectedValue('screen_size', '15-16'),
                portability: getSelectedValue('portability', 'medium'),
                brand: brandVal,
                budget: parseInt(budgetInput ? budgetInput.value : 1500, 10)
            };

            // Save payload to sessionStorage
            sessionStorage.setItem('quiz_data', JSON.stringify(payload));

            // Show loading animation
            showLoading(true);

            // Fetch and save results to sessionStorage, then redirect
            setTimeout(async () => {
                try {
                    const response = await fetch('/api/recommend', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(payload)
                    });
                    
                    const result = await response.json();

                    if (!response.ok || result.error) {
                        throw new Error(result.error || "Server error calculating recommendations");
                    }
                    
                    // Store recommendations in sessionStorage
                    sessionStorage.setItem('quiz_results', JSON.stringify(result.recommendations || []));
                    
                    // Redirect to results page
                    window.location.href = '/results';
                } catch (error) {
                    console.error('Error generating recommendations:', error);
                    showLoading(false);
                    alert(`Could not load recommendations: ${error.message}`);
                }
            }, 1200);
        }
    });

    prevBtn.addEventListener('click', (e) => {
        e.preventDefault();
        if (currentStep > 1) {
            currentStep--;
            updateWizard();
        }
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
            }, 800);
        } else {
            loadingOverlay.classList.add('hidden');
            clearInterval(statusInterval);
        }
    }
});
