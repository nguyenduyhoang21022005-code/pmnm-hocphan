from flask import Flask, request, jsonify, url_for, render_template_string, abort, redirect, make_response
import io
import csv

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

# HTML Template cho Danh sách sinh viên (Đã tích hợp Form tìm kiếm + Lọc lớp + Chống XSS)
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
        .search-box { margin-bottom: 15px; }
    </style>
</head>
<body>
    <h2>Danh sách sinh viên</h2>

    <!-- Form GET Tìm kiếm an toàn (Chống XSS) -->
    <div class="search-box">
        <form action="{{ url_for('student_list') }}" method="GET">
            {% if selected_lop %}
                <input type="hidden" name="lop" value="{{ selected_lop }}">
            {% endif %}
            <input type="text" name="q" value="{{ query }}" placeholder="Nhập tên hoặc MSSV...">
            <button type="submit">Tìm kiếm</button>
            {% if query or selected_lop %}
                <a href="{{ url_for('student_list') }}"><button type="button">Xóa bộ lọc</button></a>
            {% endif %}
        </form>
    </div>

    <!-- Thanh lọc các lớp -->
    <div class="filter-bar">
        <span>Thanh lọc: </span>
        <a href="{{ url_for('student_list', q=query) }}" class="{% if not selected_lop %}active{% endif %}">Tất cả</a>
        
        {% for lop in all_classes %}
            <a href="{{ url_for('student_list', lop=lop, q=query) }}" 
               class="{% if selected_lop.lower() == lop.lower() %}active{% endif %}">
                {{ lop }}
            </a>
        {% endfor %}
    </div>
    <br>

    <!-- Hiển thị kết quả tìm kiếm nếu có từ khóa q -->
    {% if query %}
        <p>Tìm thấy <strong>{{ students|length }}</strong> kết quả cho "<strong>{{ query }}</strong>"{% if selected_lop %} trong lớp <strong>{{ selected_lop }}</strong>{% endif %}</p>
    {% endif %}

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
                <td><a href="{{ url_for('student_detail', mssv=s.mssv) }}">{{ s.mssv }}</a></td>
                <td>{{ s.name }}</td>
                <td>{{ s.lop }}</td>
                <td>{{ s.avg }}</td>
                <td>{{ s.rank }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    {% else %}
        <p>Không có sinh viên phù hợp.</p>
    {% endif %}

    <br>
    <a href="{{ url_for('index') }}">Quay lại trang chủ</a>
</body>
</html>
"""

DETAIL_HTML = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <title>Chi tiết sinh viên - {{ student.name }}</title>
    <style>
        table, th, td { border: 1px solid black; border-collapse: collapse; padding: 8px; }
    </style>
</head>
<body>
    <h2>Thông tin sinh viên</h2>
    <p><strong>MSSV:</strong> {{ student.mssv }}</p>
    <p><strong>Họ tên:</strong> {{ student.name }}</p>
    <p><strong>Lớp:</strong> <a href="{{ url_for('student_list', lop=student.lop) }}">{{ student.lop }}</a></p>
    <p><strong>Điểm TB:</strong> {{ student.avg }}</p>
    <p><strong>Xếp loại:</strong> {{ student.rank }}</p>
    <p><strong>Link rút gọn (Câu 4):</strong> <a href="{{ url_for('short_url', mssv=student.mssv) }}">{{ url_for('short_url', mssv=student.mssv, _external=True) }}</a></p>

    <h3>Bảng điểm từng học phần</h3>
    {% if scores %}
    <table>
        <thead>
            <tr>
                <th>Môn học</th>
                <th>Điểm số</th>
            </tr>
        </thead>
        <tbody>
            {% for subject, score in scores.items() %}
            <tr>
                <td>{{ subject }}</td>
                <td>{{ score }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    <br>
    <a href="{{ url_for('export_csv', mssv=student.mssv) }}">Tải bảng điểm (CSV)</a>
    {% else %}
        <p>Sinh viên chưa có điểm môn nào.</p>
    {% endif %}

    <br><br>
    <p>
        <a href="{{ url_for('student_list') }}">Quay lại danh sách</a> | 
        <a href="{{ url_for('index') }}">Trang chủ</a>
    </p>
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

@app.route('/')
def index():
    total_students = len(STUDENTS)
    total_classes = len(set(student["lop"] for student in STUDENTS.values()))
    
    return render_template_string(
        INDEX_HTML, 
        total_students=total_students, 
        total_classes=total_classes
    )

@app.route('/api/students')
def api_students():
    return jsonify(STUDENTS)

# Route /students xử lý cả lọc theo Lớp và Tìm kiếm theo Từ khóa (q)
@app.route('/students')
def student_list():
    lop_filter = request.args.get('lop', '').strip()
    query = request.args.get('q', '').strip()
    
    all_classes = sorted(list(set(student["lop"] for student in STUDENTS.values())))
    
    filtered_students = []
    for mssv, info in STUDENTS.items():
        # Lọc theo lớp
        if lop_filter and info["lop"].lower() != lop_filter.lower():
            continue
            
        # Lọc theo từ khóa tìm kiếm (Tên hoặc MSSV)
        if query:
            q_lower = query.lower()
            if q_lower not in info["name"].lower() and q_lower not in mssv.lower():
                continue

        filtered_students.append(process_student(mssv, info))
        
    return render_template_string(
        STUDENTS_HTML, 
        students=filtered_students, 
        all_classes=all_classes, 
        selected_lop=lop_filter,
        query=query
    )

@app.route('/students/<mssv>')
def student_detail(mssv):
    if mssv not in STUDENTS:
        abort(404, description=f"Không có sinh viên với MSSV = {mssv}.")
    
    info = STUDENTS[mssv]
    student_processed = process_student(mssv, info)
    
    return render_template_string(
        DETAIL_HTML,
        student=student_processed,
        scores=info.get("scores", {})
    )

@app.route('/sv/<mssv>')
def short_url(mssv):
    return redirect(url_for('student_detail', mssv=mssv), code=301)

@app.route('/students/<mssv>/export')
def export_csv(mssv):
    if mssv not in STUDENTS:
        abort(404, description=f"Không có sinh viên với MSSV = {mssv}.")
    
    student = STUDENTS[mssv]
    scores = student.get("scores", {})

    si = io.StringIO()
    writer = csv.writer(si)
    
    writer.writerow(['hoc_phan', 'diem'])
    
    for subject, score in scores.items():
        writer.writerow([subject, score])

    response = make_response(si.getvalue())
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    response.headers['Content-Disposition'] = f'attachment; filename=diem_{mssv}.csv'
    
    return response

@app.route('/search')
def search():
    query = request.args.get('q', '')
    return redirect(url_for('student_list', q=query))

if __name__ == '__main__':
    app.run(debug=True, port=8000)
