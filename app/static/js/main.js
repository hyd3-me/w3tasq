// app/static/js/main.js

// --- Global variables for pagination state ---
// Grouped together for better readability
let paginationState = {
    current_cursor: null,
    is_loading: false,
    has_more_tasks: true
};

// --- Helper function to escape HTML ---
function escapeHtml(unsafe) {
    if (typeof unsafe !== 'string') return unsafe;
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "<")
        .replace(/>/g, ">")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// --- Helper function to format a single task ---
function formatTaskHtml(task) {
    let createdAtStr = 'Unknown date';
    if (task.created_at) {
        try {
            const date = new Date(task.created_at);
            createdAtStr = date.toLocaleString();
        } catch (e) {
            createdAtStr = task.created_at;
        }
    }

    const priorityClass = `priority-${task.priority}`;

    let priorityText = 'Unknown';
    switch (task.priority) {
        case 1: priorityText = '🔴 High'; break;
        case 2: priorityText = '🟡 Medium'; break;
        case 3: priorityText = '⚪ Low'; break;
        default: priorityText = `Priority ${task.priority}`;
    }

    return `
        <div class="task-item ${priorityClass}">
            <h4>${escapeHtml(task.title)}</h4>
            ${task.description ? `<p>${escapeHtml(task.description)}</p>` : ''}
            <div style="display: flex; justify-content: space-between; font-size: 0.9em; color: #666;">
                <span>Priority: ${priorityText}</span>
                <span>Created: ${createdAtStr}</span>
            </div>
            ${task.deadline ? `<div style="font-size: 0.8em; color: #888; margin-top: 5px;">Deadline: ${new Date(task.deadline).toLocaleString()}</div>` : ''}
        </div>
    `;
}

// --- Function to switch between sections ---
function switchSection(showSectionId) {
    // Hide all sections
    document.querySelectorAll('.section').forEach(section => {
        section.classList.remove('active');
    });

    // Remove active class from all navigation buttons
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.classList.remove('active');
    });

    // Show the required section
    const showSection = document.getElementById(showSectionId);
    if (showSection) {
        showSection.classList.add('active');
    }

    // Make the corresponding navigation button active
    let activeBtnId;
    if (showSectionId === 'addTaskSection') {
        activeBtnId = 'showAddTaskBtn';
    } else if (showSectionId === 'tasksSection') {
        activeBtnId = 'showTasksBtn';
        // Automatically load tasks when switching to the tasks section
        loadUserTasks(true); // true = reset cursor
    }

    const activeBtn = document.getElementById(activeBtnId);
    if (activeBtn) {
        activeBtn.classList.add('active');
    }
}

// --- Function to log out ---
const logoutButton = document.getElementById('logoutBtn');
if (logoutButton) {
    logoutButton.addEventListener('click', function (e) {
        e.preventDefault();

        fetch('/api/auth/logout', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    window.location.href = '/login';
                } else {
                    alert('Logout failed: ' + data.message);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Network error occurred during logout');
            });
    });
}

// --- Function to create a task ---
const taskForm = document.getElementById('taskForm');
if (taskForm) {
    taskForm.addEventListener('submit', function (e) {
        e.preventDefault();

        const title = document.getElementById('taskTitle').value.trim();
        const description = document.getElementById('taskDescription').value.trim();
        const priority = parseInt(document.getElementById('taskPriority').value);
        const deadline = document.getElementById('taskDeadline').value;

        if (!title) {
            alert('Please enter a task title');
            return;
        }

        const taskData = {
            title: title,
            description: description,
            priority: priority,
            status: 0
        };

        if (deadline) {
            taskData.deadline = deadline;
        }

        fetch('/api/tasks', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(taskData)
        })
            .then(response => {
                if (!response.ok) {
                    return response.json().then(err => Promise.reject(err));
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    alert('Task created successfully!');
                    document.getElementById('taskTitle').value = '';
                    document.getElementById('taskDescription').value = '';
                    document.getElementById('taskDeadline').value = '';
                    // Do not reset priority, leave as default
                    document.getElementById('taskTitle').focus();
                    // After creating a task, you can automatically switch to the list
                    // switchSection('tasksSection');
                } else {
                    alert('Error creating task: ' + (data.error || 'Unknown error'));
                }
            })
            .catch(error => {
                console.error('Error:', error);
                if (error.error) {
                    alert('Error creating task: ' + error.error);
                } else {
                    alert('Network error occurred. Please try again.');
                }
            });
    });
}

// --- Helper function to load tasks (common logic) ---
function fetchTasks(cursor = null) {
    let url = `/api/tasks`;
    if (cursor !== null) {
        url += `?cursor=${cursor}`;
    }

    return fetch(url)
        .then(response => {
            if (!response.ok) {
                if (response.status === 401) {
                    throw new Error('Not authenticated');
                }
                return response.json().then(err => Promise.reject(err));
            }
            return response.json();
        });
}

// --- Function to display tasks (for initial load) ---
function displayTasks(tasks) {
    const container = document.getElementById('tasksContainer');
    if (!container) return;

    if (!tasks || tasks.length === 0) {
        container.innerHTML = '<p class="text-center">No tasks found.</p>';
        paginationState.has_more_tasks = false;
        return;
    }

    let tasksHtml = '';
    tasks.forEach(task => {
        tasksHtml += formatTaskHtml(task);
    });

    container.innerHTML = tasksHtml;

    // If there are more tasks, add scroll listener
    if (paginationState.has_more_tasks) {
        container.addEventListener('scroll', checkScroll);
        // Also check immediately after the first load
        setTimeout(checkScroll, 100);
    }
}

// --- Function to append tasks to the end of the list ---
function appendTasks(tasks) {
    const container = document.getElementById('tasksContainer');
    if (!container) return;

    if (tasks.length === 0) {
        // If there are no tasks, show a message (only if it's the first load)
        if (container.children.length === 0 || container.querySelector('.text-center')) {
            container.innerHTML = '<p class="text-center">No tasks found.</p>';
        }
        paginationState.has_more_tasks = false;
        return;
    }

    let tasksHtml = '';
    tasks.forEach(task => {
        tasksHtml += formatTaskHtml(task);
    });

    // Add HTML to the end of the container
    container.insertAdjacentHTML('beforeend', tasksHtml);

    // If there are no more tasks, show a message
    if (!paginationState.has_more_tasks) {
        const endMsg = document.createElement('p');
        endMsg.className = 'text-center';
        endMsg.style.marginTop = '20px';
        endMsg.style.color = '#666';
        endMsg.textContent = 'No more tasks to load.';
        container.appendChild(endMsg);
    }
}

// --- Updated function to load tasks (for initial load) ---
function loadUserTasks(reset_cursor = true) {
    const container = document.getElementById('tasksContainer');
    if (!container) return;

    // Reset state if needed
    if (reset_cursor) {
        paginationState.current_cursor = null;
        paginationState.has_more_tasks = true;
        paginationState.is_loading = false;
        container.innerHTML = '<div class="loading">Loading tasks...</div>';
    }

    fetchTasks(paginationState.current_cursor)
        .then(data => {
            // Update pagination state
            paginationState.has_more_tasks = data.pagination.has_more;
            paginationState.current_cursor = data.pagination.next_cursor;

            // If reset, replace the entire content
            if (reset_cursor) {
                displayTasks(data.tasks);
            } else {
                // Otherwise, add to existing
                appendTasks(data.tasks);
            }

            paginationState.is_loading = false;
        })
        .catch(error => {
            console.error('Error loading tasks:', error);
            container.innerHTML = '<p class="text-center" style="color: red;">Error loading tasks: ' + (error.error || error.message || 'Unknown error') + '</p>';
            paginationState.is_loading = false;
        });
}

// --- Function to check if more tasks need to be loaded ---
function checkScroll() {
    if (paginationState.is_loading || !paginationState.has_more_tasks) return;

    const container = document.getElementById('tasksContainer');
    if (!container) return;

    // Check if we have scrolled to the end of the container
    // Use getBoundingClientRect for precise calculation
    const rect = container.getBoundingClientRect();
    const isVisible = rect.top < window.innerHeight && rect.bottom >= 0;

    // Alternative: load when the user approaches the end
    // Check how much the container is scrolled
    const scrollTop = container.scrollTop;
    const scrollHeight = container.scrollHeight;
    const clientHeight = container.clientHeight;

    // If less than 100px to the end, load more
    if (scrollHeight - scrollTop - clientHeight < 100) {
        loadMoreTasks();
    }
}

// --- Function to load the next batch of tasks ---
function loadMoreTasks() {
    if (paginationState.is_loading || !paginationState.has_more_tasks) return;
    paginationState.is_loading = true;

    const container = document.getElementById('tasksContainer');
    if (!container) {
        paginationState.is_loading = false;
        return;
    }

    // Show loading indicator at the bottom
    const loader = document.createElement('div');
    loader.id = 'scroll-loader';
    loader.className = 'loading';
    loader.textContent = 'Loading more tasks...';
    loader.style.textAlign = 'center';
    loader.style.padding = '20px';
    loader.style.color = '#666';
    container.appendChild(loader);

    fetchTasks(paginationState.current_cursor)
        .then(data => {
            // Remove loading indicator
            const loaderElement = document.getElementById('scroll-loader');
            if (loaderElement) loaderElement.remove();

            // Update pagination state
            paginationState.has_more_tasks = data.pagination.has_more;
            paginationState.current_cursor = data.pagination.next_cursor;

            // Add new tasks to the end of the existing list
            appendTasks(data.tasks);

            paginationState.is_loading = false;
        })
        .catch(error => {
            console.error('Error loading more tasks:', error);
            // Remove loading indicator in case of error
            const loaderElement = document.getElementById('scroll-loader');
            if (loaderElement) loaderElement.remove();

            // Show error message
            const errorMsg = document.createElement('p');
            errorMsg.className = 'text-center';
            errorMsg.style.color = 'red';
            errorMsg.textContent = 'Error loading tasks: ' + (error.error || error.message || 'Unknown error');
            container.appendChild(errorMsg);

            paginationState.is_loading = false;
        });
}

// --- Function to toggle theme ---
function initThemeToggle() {
    // Execute the logic directly, as this function is called from the main DOMContentLoaded
    const toggleButton = document.getElementById('themeToggle');
    const body = document.body;

    if (toggleButton) {
        toggleButton.addEventListener('click', () => {
            body.classList.toggle('dark-theme');
            // Save user's choice to localStorage
            const isDark = body.classList.contains('dark-theme');
            localStorage.setItem('theme', isDark ? 'dark' : 'light');
        });
    }

    // Check saved theme on page load
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
        body.classList.add('dark-theme');
    } else if (savedTheme === 'light') {
        body.classList.remove('dark-theme');
    }
    // Rest of the theme initialization logic...
}

// --- Initialize all functions after DOM load ---
document.addEventListener('DOMContentLoaded', function () {
    // Initialize the theme toggle
    initThemeToggle();

    // --- Click handlers for navigation buttons ---
    const showAddTaskBtn = document.getElementById('showAddTaskBtn');
    const showTasksBtn = document.getElementById('showTasksBtn');

    if (showAddTaskBtn) {
        showAddTaskBtn.addEventListener('click', function (e) {
            e.preventDefault();
            switchSection('addTaskSection');
        });
    }

    if (showTasksBtn) {
        showTasksBtn.addEventListener('click', function (e) {
            e.preventDefault();
            switchSection('tasksSection');
        });
    }

    // Handler for the refresh tasks button
    const loadTasksBtn = document.getElementById('loadTasksBtn');
    if (loadTasksBtn) {
        loadTasksBtn.addEventListener('click', function (e) {
            e.preventDefault();
            // Refresh the first batch of tasks
            loadUserTasks(true); // true = reset cursor
        });
    }

    // Add global scroll handler (in case the container itself is not scrollable)
    window.addEventListener('scroll', checkScroll);
});