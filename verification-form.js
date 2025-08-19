// E-Commerce Platform Verification Form JavaScript

// Verification data structure
const verificationData = {
    "Authentication & User Management": {
        "User Registration & Login": [
            "User registration form (frontend)",
            "Email validation",
            "Password strength validation", 
            "User login form (frontend)",
            "JWT token generation (backend)",
            "JWT token validation (backend)",
            "Remember me functionality",
            "Logout functionality",
            "Session management"
        ],
        "Password Management": [
            "Forgot password functionality",
            "Password reset via email",
            "Change password (logged in users)",
            "Password encryption/hashing"
        ],
        "User Profiles": [
            "User profile creation",
            "Profile editing",
            "Profile picture upload",
            "User preferences settings",
            "Account deactivation"
        ],
        "Role-Based Access Control": [
            "Customer role permissions",
            "Seller role permissions", 
            "Admin role permissions",
            "Role-based route protection",
            "API endpoint permissions"
        ]
    },
    "Product Management": {
        "Product Catalog": [
            "Product listing page",
            "Product detail page",
            "Product image display",
            "Product image zoom/gallery",
            "Product variants (size, color, etc.)",
            "Product reviews and ratings",
            "Related products display",
            "Recently viewed products"
        ],
        "Category Management": [
            "Category hierarchy display",
            "Category navigation",
            "Category-based filtering",
            "Breadcrumb navigation",
            "Category landing pages"
        ],
        "Product Search & Filtering": [
            "Search bar functionality",
            "Auto-complete suggestions",
            "Advanced search filters",
            "Price range filtering",
            "Brand filtering",
            "Sort by (price, popularity, rating)",
            "Search results pagination",
            "No results handling"
        ],
        "Inventory Management": [
            "Stock level display",
            "Out of stock handling",
            "Low stock alerts",
            "Inventory tracking",
            "Stock updates on orders"
        ]
    },
    "Shopping Cart & Wishlist": {
        "Shopping Cart": [
            "Add to cart functionality",
            "Cart item quantity update",
            "Remove from cart",
            "Cart persistence (logged in)",
            "Cart persistence (guest users)",
            "Cart total calculation",
            "Tax calculation",
            "Shipping cost calculation",
            "Cart page display",
            "Mini cart widget"
        ],
        "Wishlist": [
            "Add to wishlist",
            "Remove from wishlist",
            "Wishlist page display",
            "Move from wishlist to cart",
            "Wishlist sharing",
            "Wishlist persistence"
        ],
        "Saved Items": [
            "Save for later functionality",
            "Saved items management",
            "Move saved items to cart"
        ]
    },
    "Checkout Process": {
        "Checkout Flow": [
            "Checkout initiation",
            "Guest checkout option",
            "Login/register during checkout",
            "Multi-step checkout process",
            "Checkout progress indicator",
            "Order summary display"
        ],
        "Address Management": [
            "Shipping address form",
            "Billing address form",
            "Address validation",
            "Multiple address support",
            "Default address setting",
            "Address book management"
        ],
        "Shipping Options": [
            "Shipping method selection",
            "Shipping cost calculation",
            "Delivery date estimation",
            "Express shipping options",
            "Free shipping thresholds"
        ]
    },
    "Payment Processing": {
        "Payment Methods": [
            "Credit/Debit card payment",
            "Razorpay integration",
            "Stripe integration",
            "Wallet payment",
            "Gift card payment",
            "Cash on delivery (COD)",
            "EMI options"
        ],
        "Payment Security": [
            "Secure payment forms",
            "Payment data encryption",
            "PCI compliance",
            "3D Secure authentication",
            "Payment failure handling"
        ],
        "Multi-Currency Support": [
            "Currency selection",
            "Currency conversion",
            "Local payment methods",
            "Currency-specific pricing"
        ]
    },
    "Order Management": {
        "Order Creation": [
            "Order placement",
            "Order confirmation email",
            "Order number generation",
            "Inventory deduction",
            "Order status initialization"
        ],
        "Order Tracking": [
            "Order status updates",
            "Order tracking page",
            "Shipping notifications",
            "Delivery notifications",
            "Order timeline display"
        ],
        "Order History": [
            "Customer order history",
            "Order details view",
            "Reorder functionality",
            "Order search/filtering",
            "Download invoices"
        ]
    },
    "Seller Management": {
        "Seller Registration": [
            "Seller registration form",
            "KYC document upload",
            "Business verification",
            "Seller approval process",
            "Seller onboarding"
        ],
        "Seller Dashboard": [
            "Sales analytics",
            "Order management",
            "Product management",
            "Inventory management",
            "Revenue tracking"
        ],
        "Product Management (Seller)": [
            "Product upload",
            "Product editing",
            "Product image upload",
            "Bulk product upload",
            "Product approval process"
        ]
    },
    "Admin Panel": {
        "Dashboard": [
            "Admin dashboard",
            "Sales analytics",
            "User analytics",
            "Revenue reports",
            "Performance metrics"
        ],
        "User Management": [
            "User list/search",
            "User profile management",
            "User role assignment",
            "User activity logs",
            "User suspension/activation"
        ],
        "Product Management": [
            "Product approval/rejection",
            "Category management",
            "Brand management",
            "Bulk product operations",
            "Product analytics"
        ]
    }
};

let verificationState = {};
let totalItems = 0;

// Initialize the form
function initializeForm() {
    const formContent = document.getElementById('formContent');
    let itemId = 0;

    Object.keys(verificationData).forEach(moduleName => {
        const moduleDiv = document.createElement('div');
        moduleDiv.className = 'module-section';
        
        const moduleHeader = document.createElement('div');
        moduleHeader.className = 'module-header';
        moduleHeader.onclick = () => toggleModule(moduleName);
        
        const moduleTitle = document.createElement('h2');
        moduleTitle.innerHTML = `📋 ${moduleName}`;
        
        const moduleProgress = document.createElement('div');
        moduleProgress.className = 'module-progress';
        moduleProgress.id = `progress-${moduleName.replace(/\s+/g, '-')}`;
        moduleProgress.textContent = '0/0';
        
        moduleHeader.appendChild(moduleTitle);
        moduleHeader.appendChild(moduleProgress);
        
        const moduleContent = document.createElement('div');
        moduleContent.className = 'module-content';
        moduleContent.id = `content-${moduleName.replace(/\s+/g, '-')}`;
        
        Object.keys(verificationData[moduleName]).forEach(subsectionName => {
            const subsectionDiv = document.createElement('div');
            subsectionDiv.className = 'subsection';
            
            const subsectionTitle = document.createElement('h3');
            subsectionTitle.textContent = subsectionName;
            subsectionDiv.appendChild(subsectionTitle);
            
            verificationData[moduleName][subsectionName].forEach(item => {
                const itemDiv = document.createElement('div');
                itemDiv.className = 'verification-item';
                itemDiv.dataset.itemId = itemId;
                
                const statusSelector = document.createElement('div');
                statusSelector.className = 'status-selector';
                
                const statuses = [
                    { value: 'working', label: '✅', class: 'status-working' },
                    { value: 'partial', label: '⚠️', class: 'status-partial' },
                    { value: 'not-working', label: '❌', class: 'status-not-working' },
                    { value: 'pending', label: '🔄', class: 'status-pending' }
                ];
                
                statuses.forEach(status => {
                    const radio = document.createElement('input');
                    radio.type = 'radio';
                    radio.name = `item-${itemId}`;
                    radio.value = status.value;
                    radio.className = 'status-radio';
                    radio.onchange = () => updateStatus(itemId, status.value);
                    
                    const label = document.createElement('label');
                    label.className = `status-label ${status.class}`;
                    label.textContent = status.label;
                    label.onclick = () => radio.click();
                    
                    statusSelector.appendChild(radio);
                    statusSelector.appendChild(label);
                });
                
                const itemDescription = document.createElement('div');
                itemDescription.className = 'item-description';
                itemDescription.textContent = item;
                
                const notesInput = document.createElement('input');
                notesInput.type = 'text';
                notesInput.className = 'notes-input';
                notesInput.placeholder = 'Notes/Issues...';
                notesInput.onchange = () => updateNotes(itemId, notesInput.value);
                
                itemDiv.appendChild(statusSelector);
                itemDiv.appendChild(itemDescription);
                itemDiv.appendChild(notesInput);
                
                subsectionDiv.appendChild(itemDiv);
                
                verificationState[itemId] = {
                    module: moduleName,
                    subsection: subsectionName,
                    item: item,
                    status: null,
                    notes: ''
                };
                
                itemId++;
                totalItems++;
            });
            
            moduleContent.appendChild(subsectionDiv);
        });
        
        moduleDiv.appendChild(moduleHeader);
        moduleDiv.appendChild(moduleContent);
        formContent.appendChild(moduleDiv);
    });
    
    document.getElementById('totalItems').textContent = totalItems;
    updateStats();
    setupSearch();
}

function toggleModule(moduleName) {
    const content = document.getElementById(`content-${moduleName.replace(/\s+/g, '-')}`);
    content.classList.toggle('active');
}

function expandAll() {
    document.querySelectorAll('.module-content').forEach(content => {
        content.classList.add('active');
    });
}

function collapseAll() {
    document.querySelectorAll('.module-content').forEach(content => {
        content.classList.remove('active');
    });
}

function updateStatus(itemId, status) {
    verificationState[itemId].status = status;
    updateStats();
    updateModuleProgress();
}

function updateNotes(itemId, notes) {
    verificationState[itemId].notes = notes;
}

function updateStats() {
    const stats = {
        working: 0,
        partial: 0,
        'not-working': 0,
        pending: 0
    };

    Object.values(verificationState).forEach(item => {
        if (item.status) {
            stats[item.status]++;
        }
    });

    document.getElementById('workingCount').textContent = stats.working;
    document.getElementById('partialCount').textContent = stats.partial;
    document.getElementById('notWorkingCount').textContent = stats['not-working'];
    document.getElementById('pendingCount').textContent = stats.pending;

    const completed = stats.working + stats.partial + stats['not-working'] + stats.pending;
    const progress = (completed / totalItems) * 100;
    document.getElementById('progressFill').style.width = `${progress}%`;
}

function updateModuleProgress() {
    Object.keys(verificationData).forEach(moduleName => {
        const moduleItems = Object.values(verificationState).filter(item => item.module === moduleName);
        const completedItems = moduleItems.filter(item => item.status).length;
        const totalModuleItems = moduleItems.length;
        
        const progressElement = document.getElementById(`progress-${moduleName.replace(/\s+/g, '-')}`);
        if (progressElement) {
            progressElement.textContent = `${completedItems}/${totalModuleItems}`;
        }
    });
}

function setupSearch() {
    const searchBox = document.getElementById('searchBox');
    searchBox.addEventListener('input', function() {
        const searchTerm = this.value.toLowerCase();
        document.querySelectorAll('.verification-item').forEach(item => {
            const description = item.querySelector('.item-description').textContent.toLowerCase();
            if (description.includes(searchTerm)) {
                item.classList.remove('hidden');
                item.classList.add('highlight');
            } else {
                if (searchTerm === '') {
                    item.classList.remove('hidden', 'highlight');
                } else {
                    item.classList.add('hidden');
                    item.classList.remove('highlight');
                }
            }
        });
    });
}

function exportToJSON() {
    const data = {
        timestamp: new Date().toISOString(),
        totalItems: totalItems,
        verificationState: verificationState,
        summary: getSummary()
    };
    
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `ecommerce-verification-${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
}

function exportToCSV() {
    let csv = 'Module,Subsection,Item,Status,Notes\n';
    
    Object.values(verificationState).forEach(item => {
        csv += `"${item.module}","${item.subsection}","${item.item}","${item.status || 'Not Set'}","${item.notes}"\n`;
    });
    
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `ecommerce-verification-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
}

function saveProgress() {
    const data = {
        timestamp: new Date().toISOString(),
        verificationState: verificationState
    };
    localStorage.setItem('ecommerce-verification-progress', JSON.stringify(data));
    alert('Progress saved successfully!');
}

function loadProgress() {
    const saved = localStorage.getItem('ecommerce-verification-progress');
    if (saved) {
        const data = JSON.parse(saved);
        verificationState = data.verificationState;
        
        // Update UI
        Object.keys(verificationState).forEach(itemId => {
            const item = verificationState[itemId];
            if (item.status) {
                const radio = document.querySelector(`input[name="item-${itemId}"][value="${item.status}"]`);
                if (radio) radio.checked = true;
            }
            if (item.notes) {
                const notesInput = document.querySelector(`[data-item-id="${itemId}"] .notes-input`);
                if (notesInput) notesInput.value = item.notes;
            }
        });
        
        updateStats();
        updateModuleProgress();
        alert('Progress loaded successfully!');
    } else {
        alert('No saved progress found!');
    }
}

function getSummary() {
    const stats = {
        working: 0,
        partial: 0,
        'not-working': 0,
        pending: 0,
        total: totalItems
    };

    Object.values(verificationState).forEach(item => {
        if (item.status) {
            stats[item.status]++;
        }
    });

    return stats;
}

// Initialize the form when page loads
document.addEventListener('DOMContentLoaded', initializeForm);
