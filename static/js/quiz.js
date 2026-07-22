document.addEventListener('DOMContentLoaded', () => {
    // Elements
    const form = document.getElementById('recommend-form');
    const prevBtn = document.getElementById('prev-btn');
    const nextBtn = document.getElementById('next-btn');
    const progressEl = document.getElementById('quiz-progress-bar');
    const indicatorEl = document.getElementById('quiz-step-indicator');
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
    const totalSteps = 6;

    function updateWizard() {
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
            prevBtn.classList.add('opacity-40', 'pointer-events-none');
        } else {
            prevBtn.classList.remove('opacity-40', 'pointer-events-none');
        }

        // Change button text on final step
        if (currentStep === totalSteps) {
            nextBtn.innerHTML = `Review Recommendations <span class="material-symbols-outlined text-[18px]">check</span>`;
            nextBtn.className = "px-8 py-3 bg-jod-green text-white rounded-full font-label-md text-label-md font-semibold flex items-center justify-center gap-2 hover:bg-jod-green-dark transition-all hover:scale-[1.02] active:scale-95 cursor-pointer";
        } else {
            nextBtn.innerHTML = `Next Step <span class="material-symbols-outlined text-[18px]">arrow_forward</span>`;
            nextBtn.className = "px-8 py-3 bg-electric-blue text-white rounded-full font-label-md text-label-md font-semibold flex items-center justify-center gap-2 hover:bg-electric-blue-dark transition-all hover:scale-[1.02] active:scale-95 cursor-pointer";
        }

        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    // Initial step setup
    updateWizard();

    // Event Handlers
    nextBtn.addEventListener('click', (e) => {
        e.preventDefault();

        if (currentStep < totalSteps) {
            currentStep++;
            updateWizard();
        } else {
            // Submit form logic / redirect to results page
            const payload = {
                use_case: document.querySelector('input[name="use_case"]:checked').value,
                performance: document.querySelector('input[name="performance"]:checked').value,
                screen_size: document.querySelector('input[name="screen_size"]:checked').value,
                portability: document.querySelector('input[name="portability"]:checked').value,
                brand: document.querySelector('input[name="brand"]:checked').value,
                budget: parseInt(budgetInput.value, 10)
            };

            // Save payload to sessionStorage (for sidebar display on results page)
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
                    
                    // Store recommendations in sessionStorage
                    sessionStorage.setItem('quiz_results', JSON.stringify(result.recommendations || []));
                    
                    // Redirect to results page
                    window.location.href = '/results';
                } catch (error) {
                    console.error('Error generating recommendations:', error);
                    showLoading(false);
                    alert("Could not load recommendations. Please try again.");
                }
            }, 2000);
        }
    });

    prevBtn.addEventListener('click', (e) => {
        e.preventDefault();
        if (currentStep > 1) {
            currentStep--;
            updateWizard();
        }
    });

    // Loading overlay
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
