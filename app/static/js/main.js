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

    // const priorityClass = `priority-${task.priority}`;

    let priorityText = 'Unknown';
    switch (task.priority) {
        case 1: priorityText = '🔴 High'; break;
        case 2: priorityText = '🟡 Medium'; break;
        case 3: priorityText = '⚪ Low'; break;
        default: priorityText = `Priority ${task.priority}`;
    }

    // Determine if the task is completed for initial UI state
    const isCompleted = task.status === 1;
    const checkboxCheckedAttr = isCompleted ? ' checked' : '';
    const taskCompletedClass = isCompleted ? ' completed' : ''; // Add class if completed

    return `
        <div class="task-item priority-${task.priority}${taskCompletedClass}" data-task-id="${task.id}">
            <h4>
            <input type="checkbox" id="task-complete-checkbox-${task.id}" class="task-complete-checkbox" data-task-id="${task.id}"${checkboxCheckedAttr}>
            ${escapeHtml(task.title)}
            </h4>
            ${task.description ? `<p>${escapeHtml(task.description)}</p>` : ''}
            <div class="task-meta">
                <span>${createdAtStr}</span>
            </div>
            ${task.deadline ? `<div style="font-size: 0.8em; color: #888; margin-top: 5px;">Deadline: ${new Date(task.deadline).toLocaleString()}</div>` : ''}
            <!-- Loading indicator for task update -->
            <div class="task-loading-spinner" style="display: none; font-size: 0.8em; color: #666; margin-top: 5px;">
                Updating...
            </div>
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
                    updateMarquee('Logout failed: ' + data.message);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                updateMarquee('Network error occurred during logout');
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
            updateMarquee('Please enter a task title');
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
                    updateMarquee(`Task ${data.task.id} created successfully!`);
                    document.getElementById('taskTitle').value = '';
                    document.getElementById('taskDescription').value = '';
                    document.getElementById('taskDeadline').value = '';
                    // Do not reset priority, leave as default
                    document.getElementById('taskTitle').focus();
                    // After creating a task, you can automatically switch to the list
                    // switchSection('tasksSection');
                } else {
                    updateMarquee('Error creating task: ' + (data.error || 'Unknown error'));
                }
            })
            .catch(error => {
                console.error('Error:', error);
                if (error.error) {
                    updateMarquee('Error creating task: ' + error.error);
                } else {
                    updateMarquee('Network error occurred. Please try again.');
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

    // Attach event listeners to the newly rendered checkboxes
    attachTaskCheckboxListeners();

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

    // Attach event listeners to the newly appended checkboxes
    attachTaskCheckboxListeners();

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
        paginationState.is_loading = true;
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

// --- UPDATED FUNCTION: Check if we need to load more tasks based on window scroll ---
function checkWindowScroll() {
    // Assume pagination is managed by the global paginationState object
    if (paginationState.is_loading || !paginationState.has_more_tasks) return;

    const container = document.getElementById('tasksContainer');
    if (!container) return;

    // --- Logic 1: Check if we are near the bottom of the page ---
    // This checks the distance from the current scroll position to the bottom of the document
    const scrollTop = window.scrollY || document.documentElement.scrollTop;
    const windowHeight = window.innerHeight;
    const documentHeight = document.documentElement.scrollHeight;

    // If we are within N pixels of the bottom of the document, load more
    const distanceFromBottom = documentHeight - (scrollTop + windowHeight);
    const thresholdPixels = 100; // pixels from the bottom

    if (distanceFromBottom <= thresholdPixels) {
        loadMoreTasks();
        return; // Exit to prevent multiple calls
    }

    // --- Logic 2: Alternative - Check distance to the bottom of the tasks container ---
    // Sometimes more precise if you want to trigger loading before reaching the absolute page bottom
    /*
    const containerRect = container.getBoundingClientRect();
    const containerBottomRelativeToViewport = containerRect.bottom; // Bottom edge of container in viewport
    const viewportHeight = window.innerHeight;

    // If the bottom of the container is within N pixels of the bottom of the viewport
    if ((viewportHeight - containerBottomRelativeToViewport) < thresholdPixels) {
        loadMoreTasks();
    }
    */
}

// --- Function to load the next batch of tasks ---
function loadMoreTasks() {
    if (paginationState.is_loading || !paginationState.has_more_tasks) return;
    paginationState.is_loading = true;

    const container = document.getElementById('tasksContainer');
    if (!container) {
        paginationState.is_loading = false;
        return;
    } else {
        paginationState.is_loading = true;
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
    window.addEventListener('scroll', checkWindowScroll);
});

// Function to update marquee with a new message
    function updateMarquee(message) {
        const marqueeText = document.querySelector('.marquee-text');
        marqueeText.textContent = message; // Update animated text
        marqueeText.style.animation = 'none'; // Reset animation
        marqueeText.offsetHeight; // Trigger reflow to restart animation
        marqueeText.style.animation = 'marquee 18s linear infinite'; // Restart animation
    }

// --- Function to handle the change event on a task completion checkbox ---
function handleTaskCheckboxChange(event) {
    /**
     * Handles the logic when a user clicks the completion checkbox for a task.
     * 1. Immediately disables the checkbox to prevent double-clicks.
     * 2. Determines the new status (0=ACTIVE, 1=COMPLETED).
     * 3. Shows a loading indicator.
     * 4. Sends a PATCH request to update the task status on the server.
     * 5. On success: Updates the UI to reflect completion (strikethrough, opacity).
     * 6. On error: Reverts the checkbox state and shows an error message.
     * 7. Re-enables the checkbox in case of error or for allowing status toggle.
     */
    const checkbox = event.target; // The checkbox that triggered the event

    // --- Immediate UI Feedback ---
    // 1. Disable the checkbox instantly to prevent multiple rapid clicks
    checkbox.disabled = true;

    const taskId = checkbox.dataset.taskId;
    const isChecked = checkbox.checked;

    // Determine the numeric status to send (0=ACTIVE, 1=COMPLETED)
    const statusToSend = isChecked ? 1 : 0;

    // Find the parent task item container
    const taskItem = checkbox.closest('.task-item');
    if (!taskItem) {
        console.error('Task item container not found for checkbox');
        return;
    }



    // 2. Show loading indicator within the task item
    const spinner = taskItem.querySelector('.task-loading-spinner');
    if (spinner) {
        spinner.style.display = 'block';
    }

    // --- Send Update Request ---
    fetch(`/api/tasks/${taskId}`, {
        method: 'PATCH',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ status: statusToSend })
    })
    .then(response => {
        // Remove loading indicator regardless of outcome
        if (spinner) spinner.style.display = 'none';

        if (!response.ok) {
            // If HTTP status is not 2xx, attempt to parse error JSON
            return response.json().then(err => Promise.reject(err));
        }
        return response.json();
    })
    .then(data => {
        if (!data.success) {
            // --- API returned success=false ---
            throw new Error(data.error || 'Unknown error from server');
            }
        // --- Success Path ---
        console.log(`Task ${taskId} status updated to ${statusToSend} on server.`);
        updateMarquee(`Task ${taskId} status updated to ${statusToSend} on server.`);

        // Update the visual state of the task item based on the new status
        if (statusToSend === 1) {
            // Mark as completed: Add visual styles
            taskItem.classList.add('completed');
            // Optional: Fade out and remove task from the list
            finalizeTaskCompletion(taskItem);
            // Better approach: Reload the task list to respect filtering
            // This ensures completed tasks are removed from the "active tasks" view
            // loadUserTasks(true); // true = reset cursor and reload first page

        } else {
            // Mark as active (undo completion): Remove visual styles
            taskItem.classList.remove('completed');
            // If we were reloading on completion, we might want to reload on un-completion too
            // to ensure it reappears correctly if filtering changes. For now, just update UI.
        }

        // Keep checkbox enabled if we allow toggling back.
        // If checkbox is kept disabled after completion, user cannot undo easily.
        // Decision: Keep enabled for flexibility.
        // checkbox.disabled = false;
    })
    .catch(error => {
        // --- Error Path ---
        console.error('Error updating task status:', error);

        // 1. Revert UI changes made optimistically or due to state mismatch
        checkbox.checked = !isChecked; // Undo the checkbox change
        if (isChecked) {
            taskItem.classList.remove('completed'); // Undo strikethrough if it was checked
        } else {
            taskItem.classList.add('completed'); // Reinstate strikethrough if it was unchecked
        }

        // 2. Re-enable the checkbox so the user can try again
        checkbox.disabled = false;

        // 3. Inform the user about the error
        updateMarquee('Error updating task status: ' + (error.message || 'Unknown error'));

    });
    // Note: There is no 'finally' block here to re-enable the checkbox,
    // as re-enabling is handled explicitly in both success and error paths.
    // This allows us to keep the checkbox disabled after a successful completion
    // if desired, or re-enable it for toggling, based on specific logic.
}

// --- Function to attach event listeners to task checkboxes ---
function attachTaskCheckboxListeners() {
    /**
     * Attaches the 'change' event listener to all task completion checkboxes
     * that do not already have a listener attached.
     * This prevents duplicate listeners when new tasks are appended.
     */
    document.querySelectorAll('.task-complete-checkbox').forEach(checkbox => {
        // Check if a listener has already been attached using a data attribute
        if (!checkbox.dataset.listenerAttached) {
            // Attach the named event handler function
            checkbox.addEventListener('change', handleTaskCheckboxChange);
            // Mark the checkbox to prevent re-attaching the listener
            checkbox.dataset.listenerAttached = 'true';
        }
    });
}
// --- NEW FUNCTION: Finalize the visual removal of a completed task ---
/**
 * Applies a fade-out animation to a task item and removes it from the DOM after the animation completes.
 * Provides visual feedback that a completed task is being removed from the list.
 * @param {HTMLElement} taskItemElement - The .task-item DOM element to animate and remove.
 */
function finalizeTaskCompletion(taskItemElement) {
    /**
     * Handles the smooth visual disappearance of a task marked as completed.
     * 1. Adds a CSS class that triggers a fade-out/shrink animation.
     * 2. Waits for the animation to finish (using setTimeout).
     * 3. Removes the task element from the DOM.
     */
    if (!taskItemElement) {
        console.warn('finalizeTaskCompletion called with null/undefined taskItemElement');
        return;
    }

    // Duration should match the CSS animation duration for consistency
    const animationDurationMs = 639; // milliseconds

    // 1. Add the CSS class to start the animation
    taskItemElement.classList.add('task-finalize-animation');

    // 2. Set a timer to remove the element after the animation is expected to finish
    setTimeout(() => {
        // 3. Remove the element from the DOM
        // Check if element is still connected before removing (good practice)
        if (taskItemElement.isConnected) {
            taskItemElement.remove();
            console.log('Task item removed from DOM after animation.');
        } else {
            console.log('Task item was already removed from DOM.');
        }
    }, animationDurationMs);
}