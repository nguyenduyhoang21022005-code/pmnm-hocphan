from flask import Flask, request, jsonify, url_for, render_template_string

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

STUDENTS = {
    "23T1020001": {
        "name": "Nguyễn Văn An", "lop": "K47A",
        "scores": {"PMMNM": 8.5, "CSDL": 7.0, "MMT": 9.0}
    },
    "23T1020002": {
        "name": "Trần Thị Bình", "lop": "K47A",
        "scores": {"PMMNM": 6.0, "CSDL": 5.5, "MMT": 7.0}
    },
    "23T1020003": {
        "name": "Lê Hoàng Cường", "lop": "K47B",
        "scores": {"PMMNM": 9.5, "CSDL": 9.0}
    },
    "23T1020004": {
        "name": "Phạm Minh Dũng", "lop": "K47B",
        "scores": {"PMMNM": 4.0, "CSDL": 3.5, "MMT": 5.0}
    },
    "23T1020005": {
        "name": "Hoàng Thu Hà", "lop": "K47A",
        "scores": {}
    },
    "23T1020006": {
        "name": "Võ Quốc Khánh", "lop": "K47C",
        "scores": {"PMMNM": 7.5, "MMT": 8.0}
    }
}

INDEX_HTML = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <title>Trang chủ</title>
</head>
<body>
    <h1>Thống kê tổng quan</h1>
    <p>Tổng số sinh viên: <strong>{{ total_students }}</strong></p>
    <p>Số lớp (không trùng): <strong>{{ total_classes }}</strong></p>
    
    <p>
        <a href="{{ url_for('student_list') }}">Xem danh sách sinh viên (/students)</a> | 
        <a href="{{ url_for('api_students') }}">Dữ liệu API (/api/students)</a>
    </p>
</body>
</html>
"""

STUDENTS_HTML = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <title>Danh sách sinh viên</title>
    <style>
        table, th, td { border: 1px solid black; border-collapse: collapse; padding: 8px; }
        .filter-bar a { margin-right: 10px; text-decoration: none; }
        .filter-bar a.active { font-weight: bold; text-decoration: underline; color: red; }
    </style>
</head>
<body>
    <h2>Danh sách sinh viên</h2>

    <!-- Thanh lọc các lớp lấy động từ dữ liệu -->
    <div class="filter-bar">
        <span>Thanh lọc: </span>
        <a href="{{ url_for('student_list') }}" class="{% if not selected_lop %}active{% endif %}">Tất cả</a>
        
        <!-- Sử dụng url_for('student_list', lop=...) theo đúng GỢI Ý -->
        {% for lop in all_classes %}
            <a href="{{ url_for('student_list', lop=lop) }}" 
               class="{% if selected_lop.lower() == lop.lower() %}active{% endif %}">
                {{ lop }}
            </a>
        {% endfor %}
    </div>
    <br>

    {% if students %}
    <table>
        <thead>
            <tr>
                <th>MSSV</th>
                <th>Họ tên</th>
                <th>Lớp</th>
                <th>Điểm TB</th>
                <th>Xếp loại</th>
            </tr>
        </thead>
        <tbody>
            {% for s in students %}
            <tr>
                <td><a href="/students/{{ s.mssv }}">{{ s.mssv }}</a></td>
                <td>{{ s.name }}</td>
                <td>{{ s.lop }}</td>
                <td>{{ s.avg }}</td>
                <td>{{ s.rank }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    {% else %}
        <!-- Câu thông báo khi không tìm thấy kết quả -->
        <p>Không có sinh viên phù hợp.</p>
    {% endif %}

    <br>
    <a href="{{ url_for('index') }}">Quay lại trang chủ</a>
</body>
</html>
"""

def process_student(mssv, info):
    """Tính điểm TB và Xếp loại cho sinh viên"""
    scores = list(info.get("scores", {}).values())
    
    if not scores:
        avg_display = "-"
        rank_display = "-"
    else:
        avg = round(sum(scores) / len(scores), 2)
        avg_display = avg
        if avg >= 8.5:
            rank_display = "Xuất sắc"
        elif avg >= 7.0:
            rank_display = "Khá"
        elif avg >= 5.0:
            rank_display = "Trung bình"
        else:
            rank_display = "Yếu"

    return {
        "mssv": mssv,
        "name": info["name"],
        "lop": info["lop"],
        "avg": avg_display,
        "rank": rank_display
    }

# Câu 1. Trang chủ
@app.route('/')
def index():
    total_students = len(STUDENTS)
    total_classes = len(set(student["lop"] for student in STUDENTS.values()))
    
    return render_template_string(
        INDEX_HTML, 
        total_students=total_students, 
        total_classes=total_classes
    )

# Câu 1. Route API /api/students
@app.route('/api/students')
def api_students():
    return jsonify(STUDENTS)

# Câu 2. Route danh sách
@app.route('/students')
def student_list():
    lop_filter = request.args.get('lop', '').strip()
    
    all_classes = sorted(list(set(student["lop"] for student in STUDENTS.values())))
    
    filtered_students = []
    for mssv, info in STUDENTS.items():
        if lop_filter and info["lop"].lower() != lop_filter.lower():
            continue
        filtered_students.append(process_student(mssv, info))
        
    return render_template_string(
        STUDENTS_HTML, 
        students=filtered_students, 
        all_classes=all_classes, 
        selected_lop=lop_filter
    )

if __name__ == '__main__':
    app.run(debug=True, port=8000)