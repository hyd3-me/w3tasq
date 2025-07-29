// app/static/js/main.js

// Функция переключения между секциями
function switchSection(showSectionId) {
    // Скрываем все секции
    document.querySelectorAll('.section').forEach(section => {
        section.classList.remove('active');
    });
    
    // Убираем активный класс у всех кнопок навигации
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Показываем нужную секцию
    const showSection = document.getElementById(showSectionId);
    if (showSection) {
        showSection.classList.add('active');
    }
    
    // Делаем активной соответствующую кнопку навигации
    let activeBtnId;
    if (showSectionId === 'addTaskSection') {
        activeBtnId = 'showAddTaskBtn';
    } else if (showSectionId === 'tasksSection') {
        activeBtnId = 'showTasksBtn';
        // Автоматически загружаем задачи при переходе на секцию задач
        loadUserTasks();
    }
    
    const activeBtn = document.getElementById(activeBtnId);
    if (activeBtn) {
        activeBtn.classList.add('active');
    }
}

// Обработчики кликов для навигационных кнопок
document.addEventListener('DOMContentLoaded', function() {
    const showAddTaskBtn = document.getElementById('showAddTaskBtn');
    const showTasksBtn = document.getElementById('showTasksBtn');
    
    if (showAddTaskBtn) {
        showAddTaskBtn.addEventListener('click', function(e) {
            e.preventDefault();
            switchSection('addTaskSection');
        });
    }
    
    if (showTasksBtn) {
        showTasksBtn.addEventListener('click', function(e) {
            e.preventDefault();
            switchSection('tasksSection');
        });
    }
    
    // Обработчик для кнопки обновления задач
    const loadTasksBtn = document.getElementById('loadTasksBtn');
    if (loadTasksBtn) {
        loadTasksBtn.addEventListener('click', function(e) {
            e.preventDefault();
            loadUserTasks();
        });
    }
});

// Функция для выхода из системы
const logoutButton = document.getElementById('logoutBtn');
if (logoutButton) {
    logoutButton.addEventListener('click', function(e) {
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

// Функция для создания задачи
const taskForm = document.getElementById('taskForm');
if (taskForm) {
    taskForm.addEventListener('submit', function(e) {
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
            // Не сбрасываем приоритет, оставляем по умолчанию
            document.getElementById('taskTitle').focus();
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
// --- Глобальные переменные для состояния пагинации ---
let current_cursor = null;
let is_loading = false; // Флаг для предотвращения множественных запросов
let has_more_tasks = true; // Флаг, есть ли еще задачи

// --- Функция для проверки, нужно ли подгружать еще задачи ---
function checkScroll() {
    if (is_loading || !has_more_tasks) return;
    
    const container = document.getElementById('tasksContainer');
    if (!container) return;
    
    // Проверяем, докрутили ли до конца контейнера
    // Используем.getBoundingClientRect() для точного расчета
    const rect = container.getBoundingClientRect();
    const isVisible = rect.top < window.innerHeight && rect.bottom >= 0;
    
    // Альтернатива: подгружать, когда пользователь приблизился к концу
    // Проверяем, насколько прокручен контейнер
    const scrollTop = container.scrollTop;
    const scrollHeight = container.scrollHeight;
    const clientHeight = container.clientHeight;
    
    // Если до конца меньше 100px, подгружаем
    if (scrollHeight - scrollTop - clientHeight < 100) {
        loadMoreTasks();
    }
}

// --- Функция для подгрузки следующей порции задач ---
function loadMoreTasks() {
    if (is_loading || !has_more_tasks) return;
    
    is_loading = true;
    const container = document.getElementById('tasksContainer');
    if (!container) {
        is_loading = false;
        return;
    }
    
    // Показываем индикатор загрузки внизу
    const loader = document.createElement('div');
    loader.id = 'scroll-loader';
    loader.className = 'loading';
    loader.textContent = 'Loading more tasks...';
    loader.style.textAlign = 'center';
    loader.style.padding = '20px';
    loader.style.color = '#666';
    container.appendChild(loader);
    
    // Формируем URL
    let url = `/api/tasks`;
    if (current_cursor !== null) {
        url += `?cursor=${current_cursor}`;
    }
    
    fetch(url)
        .then(response => {
            // Убираем индикатор загрузки
            const loaderElement = document.getElementById('scroll-loader');
            if (loaderElement) loaderElement.remove();
            
            if (!response.ok) {
                if (response.status === 401) {
                    throw new Error('Not authenticated');
                }
                return response.json().then(err => Promise.reject(err));
            }
            return response.json();
        })
        .then(data => {
            // Обновляем состояние пагинации
            has_more_tasks = data.pagination.has_more;
            current_cursor = data.pagination.next_cursor;
            
            // Добавляем новые задачи в конец существующего списка
            appendTasks(data.tasks);
            
            is_loading = false;
        })
        .catch(error => {
            console.error('Error loading more tasks:', error);
            // Убираем индикатор загрузки в случае ошибки
            const loaderElement = document.getElementById('scroll-loader');
            if (loaderElement) loaderElement.remove();
            
            // Показываем сообщение об ошибке
            const errorMsg = document.createElement('p');
            errorMsg.className = 'text-center';
            errorMsg.style.color = 'red';
            errorMsg.textContent = 'Error loading tasks: ' + (error.error || error.message || 'Unknown error');
            container.appendChild(errorMsg);
            
            is_loading = false;
        });
}

// --- Функция для добавления задач в конец списка ---
function appendTasks(tasks) {
    const container = document.getElementById('tasksContainer');
    if (!container) return;
    
    if (tasks.length === 0) {
        // Если задач нет, показываем сообщение (только если это первая загрузка)
        if (container.children.length === 0 || container.querySelector('.text-center')) {
             container.innerHTML = '<p class="text-center">No tasks found.</p>';
        }
        has_more_tasks = false;
        return;
    }
    
    let tasksHtml = '';
    tasks.forEach(task => {
        // Форматируем задачу (тот же код, что и в displayTasks)
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
        switch(task.priority) {
            case 1: priorityText = '🔴 High'; break;
            case 2: priorityText = '🟡 Medium'; break;
            case 3: priorityText = '⚪ Low'; break;
            default: priorityText = `Priority ${task.priority}`;
        }
        
        tasksHtml += `
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
    });
    
    // Добавляем HTML в конец контейнера
    container.insertAdjacentHTML('beforeend', tasksHtml);
    
    // Если больше задач нет, показываем сообщение
    if (!has_more_tasks) {
        const endMsg = document.createElement('p');
        endMsg.className = 'text-center';
        endMsg.style.marginTop = '20px';
        endMsg.style.color = '#666';
        endMsg.textContent = 'No more tasks to load.';
        container.appendChild(endMsg);
    }
}

// --- Обновленная функция загрузки задач (для первой загрузки) ---
function loadUserTasks(reset_cursor = true) {
    const container = document.getElementById('tasksContainer');
    if (!container) return;
    
    // Сбрасываем состояние, если нужно
    if (reset_cursor) {
        current_cursor = null;
        has_more_tasks = true;
        is_loading = false;
        container.innerHTML = '<div class="loading">Loading tasks...</div>';
    }
    
    // Формируем URL
    let url = `/api/tasks`;
    if (!reset_cursor && current_cursor !== null) {
        url += `?cursor=${current_cursor}`;
    }
    
    fetch(url)
        .then(response => {
            if (!response.ok) {
                if (response.status === 401) {
                    throw new Error('Not authenticated');
                }
                return response.json().then(err => Promise.reject(err));
            }
            return response.json();
        })
        .then(data => {
            // Обновляем состояние пагинации
            has_more_tasks = data.pagination.has_more;
            current_cursor = data.pagination.next_cursor;
            
            // Если сброс, заменяем весь контент
            if (reset_cursor) {
                displayTasks(data.tasks);
            } else {
                // Иначе добавляем к существующим
                appendTasks(data.tasks);
            }
            
            is_loading = false;
        })
        .catch(error => {
            console.error('Error loading tasks:', error);
            container.innerHTML = '<p class="text-center" style="color: red;">Error loading tasks: ' + (error.error || error.message || 'Unknown error') + '</p>';
            is_loading = false;
        });
}

// --- Упрощенная функция отображения задач (для первой загрузки) ---
function displayTasks(tasks) {
    const container = document.getElementById('tasksContainer');
    if (!container) return;
    
    if (!tasks || tasks.length === 0) {
        container.innerHTML = '<p class="text-center">No tasks found.</p>';
        has_more_tasks = false;
        return;
    }
    
    let tasksHtml = '';
    tasks.forEach(task => {
        // ... (тот же код форматирования, что и в appendTasks) ...
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
        switch(task.priority) {
            case 1: priorityText = '🔴 High'; break;
            case 2: priorityText = '🟡 Medium'; break;
            case 3: priorityText = '⚪ Low'; break;
            default: priorityText = `Priority ${task.priority}`;
        }
        
        tasksHtml += `
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
    });
    
    container.innerHTML = tasksHtml;
    
    // Если есть еще задачи, добавляем слушатель прокрутки
    if (has_more_tasks) {
        container.addEventListener('scroll', checkScroll);
        // Также проверяем сразу после первой загрузки
        setTimeout(checkScroll, 100);
    }
}

// --- Обновляем обработчик клика на кнопке "My Tasks" ---
document.addEventListener('DOMContentLoaded', function() {
    // ... (другие обработчики) ...
    
    const showTasksBtn = document.getElementById('showTasksBtn');
    if (showTasksBtn) {
        showTasksBtn.addEventListener('click', function(e) {
            e.preventDefault();
            switchSection('tasksSection');
            // При переходе на секцию задач, загружаем первую порцию
            loadUserTasks(true); // true = сбросить курсор
        });
    }
    
    // ... (другие обработчики) ...
    
    // Обработчик для кнопки обновления задач (Refresh)
    const loadTasksBtn = document.getElementById('loadTasksBtn');
    if (loadTasksBtn) {
        loadTasksBtn.addEventListener('click', function(e) {
            e.preventDefault();
            // Обновляем первую порцию задач
            loadUserTasks(true); // true = сбросить курсор
        });
    }
    
    // Добавляем глобальный обработчик прокрутки окна (на случай, если контейнер не прокручивается сам)
    window.addEventListener('scroll', checkScroll);
});

function escapeHtml(unsafe) {
    if (typeof unsafe !== 'string') return unsafe;
    return unsafe
         .replace(/&/g, "&amp;")
         .replace(/</g, "<")
         .replace(/>/g, ">")
         .replace(/"/g, "&quot;")
         .replace(/'/g, "&#039;");
}