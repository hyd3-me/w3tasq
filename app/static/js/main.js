// app/static/js/main.js

// Функция для выхода из системы
document.getElementById('logoutBtn').addEventListener('click', function(e) {
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

// Функция для создания задачи
document.getElementById('taskForm').addEventListener('submit', function(e) {
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