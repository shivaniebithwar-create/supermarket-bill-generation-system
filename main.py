
import sqlite3
from pathlib import Path
from datetime import datetime

# Database file
DB_PATH = Path(__file__).resolve().parent / "supermarket.db"


# Connect to database
def connect_db():
    con = sqlite3.connect(DB_PATH)
    con.execute("PRAGMA foreign_keys = ON")
    return con


# Create tables and insert default products
def create_tables():
    with connect_db() as con:

        con.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                stock INTEGER NOT NULL
            )
        """)

        con.execute("""
            CREATE TABLE IF NOT EXISTS bills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bill_date TEXT NOT NULL,
                total REAL NOT NULL
            )
        """)

        con.execute("""
            CREATE TABLE IF NOT EXISTS bill_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bill_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                price REAL NOT NULL,
                FOREIGN KEY (bill_id) REFERENCES bills(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        """)

        default_products = [
            ("Rice", 60, 20),
            ("Sugar", 45, 15),
            ("Milk", 30, 20),
            ("Oil", 150, 10),
            ("Soap", 40, 25),
            ("Biscuits", 20, 30),
            ("Tea Powder", 120, 12),
            ("Shampoo", 90, 15)
        ]

        for name, price, stock in default_products:
            con.execute("""
                INSERT INTO products (name, price, stock)
                SELECT ?, ?, ?
                WHERE NOT EXISTS (
                    SELECT 1 FROM products WHERE name = ?
                )
            """, (name, price, stock, name))


# Add a new product
def add_product():
    try:
        name = input("Enter product name: ").strip()

        if not name:
            print("Product name cannot be empty.")
            return

        price = float(input("Enter product price: "))
        stock = int(input("Enter stock quantity: "))

        if price <= 0 or stock < 0:
            print("Invalid price or stock quantity.")
            return

        with connect_db() as con:
            con.execute(
                "INSERT INTO products (name, price, stock) VALUES (?, ?, ?)",
                (name, price, stock)
            )

        print("Product added successfully!")

    except ValueError:
        print("Please enter valid numbers.")


# View all products
def view_products():
    with connect_db() as con:
        products = con.execute(
            "SELECT id, name, price, stock FROM products ORDER BY id"
        ).fetchall()

    if not products:
        print("No products found.")
        return

    print("\n========== PRODUCT LIST ==========")
    print(f"{'ID':<5}{'Product':<18}{'Price':<12}{'Stock'}")
    print("-" * 45)

    for product_id, name, price, stock in products:
        print(f"{product_id:<5}{name:<18}Rs.{price:<9.2f}{stock}")


# Generate customer bill
def generate_bill():
    view_products()

    cart = {}

    while True:
        choice = input(
            "\nEnter product ID (0 to finish): "
        ).strip()

        if choice == "0":
            break

        try:
            product_id = int(choice)

            if product_id <= 0:
                print("Enter a valid product ID.")
                continue

            quantity = int(input("Enter quantity: "))

            if quantity <= 0:
                print("Quantity must be positive.")
                continue

            cart[product_id] = cart.get(product_id, 0) + quantity

        except ValueError:
            print("Please enter valid numbers.")

    if not cart:
        print("Bill cancelled. No items selected.")
        return

    try:
        with connect_db() as con:

            items = []
            total = 0.0

            # Check products and stock
            for product_id, quantity in cart.items():

                product = con.execute(
                    "SELECT name, price, stock FROM products WHERE id = ?",
                    (product_id,)
                ).fetchone()

                if product is None:
                    print("Product ID", product_id, "does not exist.")
                    return

                name, price, stock = product

                if quantity > stock:
                    print(
                        f"Insufficient stock for {name}. "
                        f"Available stock: {stock}"
                    )
                    return

                subtotal = price * quantity
                total += subtotal

                items.append(
                    (product_id, name, price, quantity, subtotal)
                )

            # Save bill
            cursor = con.execute(
                "INSERT INTO bills (bill_date, total) VALUES (?, ?)",
                (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), total)
            )

            bill_id = cursor.lastrowid

            # Save bill items and update stock
            for product_id, name, price, quantity, subtotal in items:

                con.execute("""
                    INSERT INTO bill_items
                    (bill_id, product_id, quantity, price)
                    VALUES (?, ?, ?, ?)
                """, (bill_id, product_id, quantity, price))

                con.execute(
                    "UPDATE products SET stock = stock - ? WHERE id = ?",
                    (quantity, product_id)
                )

        # Display bill
        print("\n========== SUPERMARKET BILL ==========")
        print("Bill Number:", bill_id)
        print("Date:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        print("--------------------------------------")

        for product_id, name, price, quantity, subtotal in items:
            print(
                f"{name} | {quantity} x Rs.{price:.2f} "
                f"= Rs.{subtotal:.2f}"
            )

        print("--------------------------------------")
        print(f"TOTAL AMOUNT: Rs.{total:.2f}")
        print("======================================")
        print("Thank you for shopping!")

    except sqlite3.Error as error:
        print("Database error:", error)


# View sales history
def view_sales():
    with connect_db() as con:
        bills = con.execute(
            "SELECT id, bill_date, total FROM bills ORDER BY id DESC"
        ).fetchall()

    if not bills:
        print("No sales records found.")
        return

    print("\n========== SALES HISTORY ==========")

    for bill_id, bill_date, total in bills:
        print(
            f"Bill #{bill_id} | {bill_date} | Rs.{total:.2f}"
        )


# Main menu
def main():
    create_tables()

    while True:
        print("\n===== SUPERMARKET MANAGEMENT SYSTEM =====")
        print("1. Add Product")
        print("2. View Products")
        print("3. Generate Bill")
        print("4. View Sales History")
        print("5. Exit")

        choice = input("Choose an option: ").strip()

        if choice == "1":
            add_product()

        elif choice == "2":
            view_products()

        elif choice == "3":
            generate_bill()

        elif choice == "4":
            view_sales()

        elif choice == "5":
            print("Thank you for using the Supermarket Management System!")
            break

        else:
            print("Invalid choice. Please select 1 to 5.")


# Start program
if __name__ == "__main__":
    main()
    

    

