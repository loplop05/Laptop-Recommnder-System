document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('recommend-form');
    const resultsSection = document.getElementById('results-section');
    const container = document.getElementById('recommendations-container');
    const loadingOverlay = document.getElementById('loading-overlay');
    const startOverBtn = document.getElementById('start-over-btn');

    // Wizard Logic
    let currentStep = 1;
    const totalSteps = 7;
    const steps = document.querySelectorAll('.step');
    const nextBtn = document.getElementById('next-btn');
    const submitBtn = document.getElementById('submit-btn');

    const stepTitles = {
        1: "Step 1: Choose Your Use Case",
        2: "Step 2: Set Your Performance",
        3: "Step 3: Choose Your Display",
        4: "Step 4: Set Your Storage",
        5: "Step 5: Choose Your Features",
        6: "Step 6: Set Your Budget",
        7: "Step 7: Final Results"
    };

    const stepSubtitles = {
        1: "Select the primary way you'll use your new laptop for the best recommendations in Jordan.",
        2: "Find the best performance within your range.",
        3: "What screen size do you prefer?",
        4: "How much storage do you need?",
        5: "Any specific features you need?",
        6: "What is your budget in JOD?",
        7: "Your curated recommendations are ready."
    };

    const stepNextButtonText = {
        1: "Continue to Performance",
        2: "Continue to Display",
        3: "Continue to Storage",
        4: "Continue to Features",
        5: "Continue to Budget",
        6: "Review Recommendations",
        7: "Generating..."
    };

    function updateWizard() {
        // Update sidebar subtitle
        const subtitle = document.querySelector('.sidebar-subtitle');
        if (subtitle) subtitle.textContent = `Step ${currentStep} of ${totalSteps}`;

        // Update main content titles
        const titleEl = document.getElementById('step-title');
        const subtitleEl = document.getElementById('step-subtitle');
        if (titleEl) titleEl.textContent = stepTitles[currentStep];
        if (subtitleEl) subtitleEl.textContent = stepSubtitles[currentStep];

        // Update steps visibility
        steps.forEach(s => s.classList.remove('active'));
        const activeStep = document.querySelector(`.step[data-step="${currentStep}"]`);
        if (activeStep) {
            activeStep.classList.add('active');
        }

        // Update sidebar nav items
        document.querySelectorAll('.nav-step').forEach((s, idx) => {
            if (idx + 1 === currentStep) {
                s.classList.add('active');
            } else {
                s.classList.remove('active');
            }
        });

        // Update button text
        if (nextBtn) {
            nextBtn.innerHTML = `${stepNextButtonText[currentStep]} <span class="arrow">→</span>`;
        }

        if (currentStep === totalSteps) {
            if (nextBtn) nextBtn.classList.add('hidden');
            if (submitBtn) submitBtn.classList.remove('hidden');
        } else {
            if (nextBtn) nextBtn.classList.remove('hidden');
            if (submitBtn) submitBtn.classList.add('hidden');
        }

        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    updateWizard();

    nextBtn.addEventListener('click', (e) => {
        e.preventDefault();
        if (currentStep < totalSteps) {
            currentStep++;
            updateWizard();
        }
    });

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        showLoading(true);
        
        // Simulated delay for AI analysis
        setTimeout(async () => {
            try {
                // In a real app, you'd fetch from /api/recommend
                const response = await fetch('/api/recommend', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        use_case: document.querySelector('input[name="use_case"]:checked').value,
                        performance: 'medium',
                        budget: 1000
                    })
                });
                const result = await response.json();
                displayRecommendations(result.recommendations || []);
            } catch (error) {
                console.error('Error fetching recommendations:', error);
            } finally {
                showLoading(false);
            }
        }, 3000);
    });

    function showLoading(show) {
        if (show) {
            loadingOverlay.classList.remove('hidden');
            startStatusUpdates();
        } else {
            loadingOverlay.classList.add('hidden');
            stopStatusUpdates();
        }
    }

    let statusInterval;
    const statuses = [
        "Scanning Amman retail stocks...",
        "Analyzing hardware benchmarks...",
        "Comparing price history...",
        "Optimizing performance ratios...",
        "Stitching recommendations..."
    ];

    function startStatusUpdates() {
        const statusEl = document.getElementById('status-update');
        let i = 0;
        statusEl.textContent = statuses[0];
        statusInterval = setInterval(() => {
            i = (i + 1) % statuses.length;
            statusEl.textContent = statuses[i];
        }, 1500);
    }

    function stopStatusUpdates() {
        clearInterval(statusInterval);
    }

    function displayRecommendations(laptops) {
        container.innerHTML = '';
        laptops.forEach((laptop, index) => {
            const card = createLaptopCard(laptop, index);
            container.appendChild(card);
        });
        document.getElementById('wizard-container').classList.add('hidden');
        resultsSection.classList.remove('hidden');
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    function createLaptopCard(laptop, index) {
        const matchScore = Math.round(laptop.match_score * 100) || (98 - index * 2);
        const imageUrl = laptop.image_url || 'https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=500&q=80';
        const isTop = index === 0;
        
        const card = document.createElement('div');
        card.className = 'laptop-card';
        card.innerHTML = `
            ${isTop ? '<div class="top-recommendation-badge">Top Recommendation</div>' : ''}
            <div class="card-image-wrapper">
                <img src="${imageUrl}" alt="${laptop.model}">
            </div>
            <div class="card-header">
                <div class="laptop-title-group">
                    <h3 class="laptop-model">${laptop.brand} ${laptop.model}</h3>
                    <div class="laptop-category">${laptop.use_case || 'High Performance'}</div>
                </div>
                <div class="match-badge-circular">
                    <span class="match-percentage">${matchScore}%</span>
                    <span class="match-label">Match</span>
                </div>
            </div>
            <div class="card-specs">
                <div class="spec-line"><span class="spec-icon">⚙️</span> ${laptop.cpu || 'Intel Core i7'}</div>
                <div class="spec-line"><span class="spec-icon">⚡</span> ${laptop.ram || '16GB'} RAM</div>
                <div class="spec-line"><span class="spec-icon">💾</span> ${laptop.ssd || '512GB'} SSD</div>
                <div class="spec-line"><span class="spec-icon">🖥️</span> ${laptop.display || '14" OLED Display'}</div>
            </div>
            <div class="ai-reasoning-box">
                <div class="ai-reasoning-title">✨ AI Reasoning</div>
                <div class="ai-reasoning-text">${laptop.reasoning || 'Perfect for your creative work and travel needs. Widely available at Jordanian retailers with excellent warranty support.'}</div>
            </div>
            <div class="card-actions">
                <button class="btn-check-price">Check Local Price</button>
                <button class="btn-view-details">View Details</button>
            </div>
        `;
        return card;
    }

    startOverBtn.addEventListener('click', () => {
        resultsSection.classList.add('hidden');
        document.getElementById('wizard-container').classList.remove('hidden');
        currentStep = 1;
        updateWizard();
    });
});
