from flask import Flask, render_template, request, jsonify
from datetime import date
import threading
import json
import os

# Remove the circular import and add AttendanceTracker class here
class AttendanceTracker:
    def __init__(self, filename="attendance.json"):
        self.filename = filename
        self.students = set()
        self.records = {}
        try:
            self.load_from_file()
        except FileNotFoundError:
            pass

    def add_student(self, name):
        self.students.add(name)
        self.save_to_file()  # Save after adding student

    def load_from_file(self):
        try:
            with open(self.filename) as f:
                data = json.load(f)
                self.students = set(data.get("students", []))
                self.records = data.get("records", {})
        except FileNotFoundError:
            self.students = set()
            self.records = {}

    def save_to_file(self):
        with open(self.filename, "w") as f:
            json.dump({
                "students": list(self.students),
                "records": self.records
            }, f, indent=2)
    
    def mark_attendance(self, date_str, student, status):
        """Mark attendance for a student on a specific date"""
        if date_str not in self.records:
            self.records[date_str] = {}
        self.records[date_str][student] = status
        self.save_to_file()
    
    def get_summary(self):
        """Calculate attendance summary for all students"""
        summary = {}
        for student in self.students:
            present_days = 0
            total_days = len(self.records)
            
            # Count present days for this student
            for date_records in self.records.values():
                if date_records.get(student) == 'present':
                    present_days += 1
            
            # Calculate percentage
            percentage = (present_days / total_days * 100) if total_days > 0 else 0
            summary[student] = {
                'present': present_days,
                'total': total_days,
                'percentage': round(percentage, 2)
            }
        return summary

# Remove this line since we defined the class above
# from attendance_system import AttendanceTracker

app = Flask(__name__, static_folder="static", template_folder="templates")
tracker = AttendanceTracker()

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/add_student', methods=['POST'])
def add_student():
    """Add a new student"""
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        
        if not name:
            return jsonify({'success': False, 'message': 'Student name cannot be empty'})
        
        if name in tracker.students:
            return jsonify({'success': False, 'message': f'Student "{name}" already exists'})
        
        tracker.add_student(name)
        return jsonify({'success': True, 'message': f'Successfully added student: {name}'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@app.route('/mark_attendance', methods=['POST'])
def mark_attendance():
    """Mark attendance for a student"""
    try:
        data = request.get_json()
        student = data.get('student', '').strip()
        status = data.get('status', 'present')
        date_str = data.get('date', date.today().isoformat())
        
        if not student:
            return jsonify({'success': False, 'message': 'Student name cannot be empty'})
        
        if student not in tracker.students:
            return jsonify({'success': False, 'message': f'Student "{student}" not found'})
        
        if status not in ['present', 'absent']:
            return jsonify({'success': False, 'message': 'Status must be "present" or "absent"'})
        
        tracker.mark_attendance(date_str, student, status)
        return jsonify({'success': True, 'message': f'Marked {student} as {status} on {date_str}'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@app.route('/get_students', methods=['GET'])
def get_students():
    """Get list of all students"""
    try:
        return jsonify({
            'success': True, 
            'students': list(tracker.students)
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@app.route('/get_summary', methods=['GET'])
def get_summary():
    """Get attendance summary"""
    try:
        summary = tracker.get_summary()
        return jsonify({
            'success': True, 
            'summary': summary
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@app.route('/get_records', methods=['GET'])
def get_records():
    """Get all attendance records"""
    try:
        return jsonify({
            'success': True, 
            'records': tracker.records
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

def create_template():
    """Create the HTML template if it doesn't exist"""
    template_dir = 'templates'
    if not os.path.exists(template_dir):
        os.makedirs(template_dir)
    
    html_content = '''<!DOCTYPE html>
<html>
<head>
    <title>Attendance System</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .section {
            margin: 20px 0;
            padding: 20px;
            border: 1px solid #ddd;
            border-radius: 5px;
        }
        h1, h2 {
            color: #333;
        }
        input, select, button {
            padding: 10px;
            margin: 5px;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
        button {
            background: #007bff;
            color: white;
            border: none;
            cursor: pointer;
        }
        button:hover {
            background: #0056b3;
        }
        .message {
            padding: 10px;
            margin: 10px 0;
            border-radius: 4px;
        }
        .success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        .error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        .student-item {
            padding: 8px;
            margin: 5px 0;
            background: #f8f9fa;
            border-left: 4px solid #007bff;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Attendance Tracking System</h1>
        
        <div class="section">
            <h2>Add Student</h2>
            <input type="text" id="studentName" placeholder="Enter student name">
            <button onclick="addStudent()">Add Student</button>
            <div id="addMessage"></div>
        </div>

        <div class="section">
            <h2>Mark Attendance</h2>
            <input type="text" id="attendanceStudent" placeholder="Student name">
            <select id="attendanceStatus">
                <option value="present">Present</option>
                <option value="absent">Absent</option>
            </select>
            <button onclick="markAttendance()">Mark Attendance</button>
            <div id="attendanceMessage"></div>
        </div>

        <div class="section">
            <h2>View Data</h2>
            <button onclick="loadStudents()">Show Students</button>
            <button onclick="loadSummary()">Show Summary</button>
            <button onclick="loadRecords()">Show Records</button>
            
            <div id="studentsList"></div>
            <div id="summaryResult"></div>
            <div id="recordsResult"></div>
        </div>
    </div>

    <script>
        function showMessage(elementId, message, isSuccess) {
            const element = document.getElementById(elementId);
            element.innerHTML = '<div class="message ' + (isSuccess ? 'success' : 'error') + '">' + message + '</div>';
            setTimeout(function() { element.innerHTML = ''; }, 5000);
        }

        async function addStudent() {
            const name = document.getElementById('studentName').value.trim();
            if (!name) {
                showMessage('addMessage', 'Please enter a student name', false);
                return;
            }

            try {
                const response = await fetch('/add_student', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({name: name})
                });
                const result = await response.json();
                showMessage('addMessage', result.message, result.success);
                if (result.success) {
                    document.getElementById('studentName').value = '';
                }
            } catch (error) {
                showMessage('addMessage', 'Error: ' + error.message, false);
            }
        }

        async function markAttendance() {
            const student = document.getElementById('attendanceStudent').value.trim();
            const status = document.getElementById('attendanceStatus').value;

            if (!student) {
                showMessage('attendanceMessage', 'Please enter a student name', false);
                return;
            }

            try {
                const response = await fetch('/mark_attendance', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({student: student, status: status})
                });
                const result = await response.json();
                showMessage('attendanceMessage', result.message, result.success);
                if (result.success) {
                    document.getElementById('attendanceStudent').value = '';
                }
            } catch (error) {
                showMessage('attendanceMessage', 'Error: ' + error.message, false);
            }
        }

        async function loadStudents() {
            try {
                const response = await fetch('/get_students');
                const result = await response.json();
                
                if (result.success) {
                    let html = '<h3>Registered Students:</h3>';
                    if (result.students.length > 0) {
                        result.students.forEach(function(student) {
                            html += '<div class="student-item">' + student + '</div>';
                        });
                    } else {
                        html += '<p>No students registered yet.</p>';
                    }
                    document.getElementById('studentsList').innerHTML = html;
                } else {
                    document.getElementById('studentsList').innerHTML = '<div class="error">' + result.message + '</div>';
                }
            } catch (error) {
                document.getElementById('studentsList').innerHTML = '<div class="error">Error loading students: ' + error.message + '</div>';
            }
        }

        async function loadSummary() {
            try {
                const response = await fetch('/get_summary');
                const result = await response.json();
                
                if (result.success) {
                    let html = '<h3>Attendance Summary:</h3>';
                    for (const student in result.summary) {
                        const data = result.summary[student];
                        html += '<div class="student-item">' +
                                '<strong>' + student + '</strong><br>' +
                                'Present: ' + data.present + '/' + data.total + ' days<br>' +
                                'Attendance: ' + data.percentage + '%' +
                                '</div>';
                    }
                    document.getElementById('summaryResult').innerHTML = html;
                } else {
                    document.getElementById('summaryResult').innerHTML = '<div class="error">' + result.message + '</div>';
                }
            } catch (error) {
                document.getElementById('summaryResult').innerHTML = '<div class="error">Error loading summary: ' + error.message + '</div>';
            }
        }

        async function loadRecords() {
            try {
                const response = await fetch('/get_records');
                const result = await response.json();
                
                if (result.success) {
                    let html = '<h3>All Records:</h3>';
                    if (Object.keys(result.records).length > 0) {
                        for (const date in result.records) {
                            html += '<h4>' + date + ':</h4>';
                            for (const student in result.records[date]) {
                                html += '<div class="student-item">' + student + ': ' + result.records[date][student] + '</div>';
                            }
                        }
                    } else {
                        html += '<p>No attendance records yet.</p>';
                    }
                    document.getElementById('recordsResult').innerHTML = html;
                } else {
                    document.getElementById('recordsResult').innerHTML = '<div class="error">' + result.message + '</div>';
                }
            } catch (error) {
                document.getElementById('recordsResult').innerHTML = '<div class="error">Error loading records: ' + error.message + '</div>';
            }
        }
    </script>
</body>
</html>'''
    
    # Write with proper encoding to avoid Unicode errors
    with open(os.path.join(template_dir, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(html_content)

if __name__ == '__main__':
    create_template()
    app.run(debug=False, host='0.0.0.0', port=5000)