from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql.expression import func
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.secret_key = 'секретный_ключ_для_сессий'

# Настройки базы данных и загрузки файлов
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dilda.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

db = SQLAlchemy(app)

# Модель товара
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    price = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(300))
    description = db.Column(db.Text)
    barcode = db.Column(db.String(50))
    category = db.Column(db.String(50))

    def __repr__(self):
        return f'<Product {self.name}>'

# Проверка допустимых расширений файлов
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Главные страницы
@app.route("/")
def index():
    random_products = Product.query.filter(Product.image_url != None).order_by(func.random()).limit(3).all()
    return render_template("index.html", random_products=random_products)

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/catalog")
def catalog():
    category = request.args.get("category")
    search = request.args.get("search")
    sort = request.args.get("sort")
    availability = request.args.get("availability")

    products = Product.query

    if category:
        products = products.filter_by(category=category)
    if search:
        products = products.filter(Product.name.ilike(f"%{search}%"))
    if availability == "available":
        products = products.filter(Product.price > 0)
    if sort == "price":
        products = products.order_by(Product.price.asc())
    elif sort == "name":
        products = products.order_by(Product.name.asc())

    return render_template("catalog.html", products=products.all())

@app.route("/contacts")
def contacts():
    return render_template("contacts.html")

# Вход и выход
@app.route("/profile", methods=["GET", "POST"])
def profile():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username == "admin" and password == "secret123":
            session["admin"] = True
            return redirect("/admin")
        else:
            return render_template("profile.html", error="Неверный логин или пароль")
    return render_template("profile.html")

@app.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect("/")

# Админка
@app.route("/admin")
def admin():
    if not session.get("admin"):
        return redirect("/profile")
    products = Product.query.all()
    return render_template("admin.html", products=products)

@app.route("/add_product", methods=["GET", "POST"])
def add_product():
    if not session.get("admin"):
        return redirect("/profile")

    if request.method == "POST":
        name = request.form["name"]
        price = float(request.form["price"])
        description = request.form.get("description")
        barcode = request.form.get("barcode")
        category = request.form.get("category")
        image = request.files.get("image")

        image_url = None
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image.save(image_path)
            image_url = f"/{image_path.replace(os.sep, '/')}"

        product = Product(
            name=name,
            price=price,
            description=description,
            barcode=barcode,
            category=category,
            image_url=image_url
        )
        db.session.add(product)
        db.session.commit()
        return redirect("/admin")

    return render_template("add_product.html")

@app.route("/admin/delete/<int:product_id>", methods=["POST"])
def delete_product(product_id):
    if not session.get("admin"):
        return redirect("/profile")

    product = Product.query.get_or_404(product_id)

    if product.image_url:
        image_path = product.image_url.lstrip("/")
        if os.path.exists(image_path):
            os.remove(image_path)

    db.session.delete(product)
    db.session.commit()
    return redirect("/admin")

@app.route("/admin/edit/<int:product_id>", methods=["GET", "POST"])
def edit_product(product_id):
    if not session.get("admin"):
        return redirect("/profile")

    product = Product.query.get_or_404(product_id)

    if request.method == "POST":
        product.name = request.form["name"]
        product.price = float(request.form["price"])
        product.description = request.form.get("description")
        product.barcode = request.form.get("barcode")

        image = request.files.get("image")
        if image and allowed_file(image.filename):
            if product.image_url:
                old_path = product.image_url.lstrip("/")
                if os.path.exists(old_path):
                    os.remove(old_path)

            filename = secure_filename(image.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image.save(image_path)
            product.image_url = f"/{image_path.replace(os.sep, '/')}"

        db.session.commit()
        return redirect("/admin")

    return render_template("edit_product.html", product=product)

# Загрузка файлов
@app.route('/static/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Корзина
@app.route("/add_to_cart/<int:product_id>", methods=["POST"])
def add_to_cart(product_id):
    cart = session.get("cart", [])
    if product_id not in cart:
        cart.append(product_id)
        session["cart"] = cart
    return redirect("/catalog")

@app.route("/remove_from_cart/<int:product_id>", methods=["POST"])
def remove_from_cart(product_id):
    cart = session.get("cart", [])
    if product_id in cart:
        cart.remove(product_id)
        session["cart"] = cart
    return redirect("/cart")

@app.route("/cart")
def cart():
    cart_ids = session.get("cart", [])
    cart_items = Product.query.filter(Product.id.in_(cart_ids)).all()
    total_price = sum(item.price for item in cart_items)
    return render_template("cart.html", cart_items=cart_items, total_price=total_price)

@app.route("/checkout", methods=["POST"])
def checkout():
    session.pop("cart", None)
    return render_template("cart.html", cart_items=[], total_price=0)

if __name__ == "__main__":
    app.run(debug=True)
