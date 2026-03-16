from flask import Flask, request, render_template_string

def fib(n):
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a

app = Flask(__name__)

html = """<!DOCTYPE html>
<html>
<head>
    <style>
        span {
            display: block;
            word-wrap: break-word;
        }
    </style>
</head>
<body>
    <h3>Fibonacchi calculator</h3>
    <form method="post">
        <input type="text" name="fibnum" required>
        <br><br>
        <input type="submit" value="Calculate">
    </form>
    <span id="result"><b>{{ result }}</b></span>
</body>
</html>"""

@app.route('/', methods=['GET', 'POST'])
def calculate():
    number = 0
    if request.method == 'POST':
        try:
            number = int(request.form['fibnum'])
            if number < 0: raise Exception
            result = fib(number)
            return render_template_string(html, result=result)
        except ValueError, Exception:
            return render_template_string(html, result="Positive integer only")

    return render_template_string(html, result="Waiting for input...")

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)