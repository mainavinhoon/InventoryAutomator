import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QMessageBox
from pymongo import MongoClient

class PetrolPumpApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Petrol Pump Management')
        self.setGeometry(100, 100, 400, 300)

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout()

        self.sync_button = QPushButton('Sync Current Inventory', self)
        self.sync_button.clicked.connect(self.sync_current_inventory)
        self.layout.addWidget(self.sync_button)

        self.central_widget.setLayout(self.layout)

        # Connect to MongoDB
        self.client = MongoClient('mongodb://localhost:27017/')
        self.db = self.client['inventory1']

    def show_message(self, message):
        msg = QMessageBox()
        msg.setText(message)
        msg.exec_()

    def sync_current_inventory(self):
        # Get the unique dates from the daily report
         # Get all unique dates from the daily report
       unique_dates = self.db.daily_report.distinct("date")

       for date in unique_dates:

         # Check if an entry for the date already exists in current_inventory
        if self.db.current_inventory.count_documents({"date": date}) > 0:
            continue  # Skip this date if an entry already exists
        
        
        # Get the latest daily report for the current date
        latest_daily_report = self.db.daily_report.find({"date": date}).sort("date", -1).limit(1).next()

        # Get the latest purchase for the current date
        latest_purchase = self.db.purchases.find({"date": date}).sort("date", -1).limit(1).next() if self.db.purchases.count_documents({"date": date}) > 0 else None

        #  Get the latest entry for the current date
        latest_entry = self.db.current_inventory.find({"date": date}).sort("date", -1).limit(1) if self.db.current_inventory.count_documents({"date": date}) > 0 else None
        
        if latest_entry:
            # Use the values from the latest entry
            regular_gallons_latest_entry = round(float(latest_entry["reguler_gallons"]),2)
            price_per_gallon_latest_entry = round(float(latest_entry["price_per_gallon"]),)
            amount_latest_entry = round(float(latest_entry["amount"]),)
        else:
            # Set default values if no previous entry exists
            regular_gallons_latest_entry = 0
            price_per_gallon_latest_entry = 0
            amount_latest_entry = 0

        # Calculate total regular gallons and total amount from the latest purchase and daily report
        total_regular_gallons_daily = round(float(latest_purchase["reguler_gallons"]),2) - round(float(latest_daily_report["reguler_gallons"]),2)

        # Calculate amount and price based on the formulas
        total_amount_purchases = round(float(latest_purchase["amount"]),2)
        total_amount_in_inventory = amount_latest_entry + total_amount_purchases
        total_regular_gallons_in_inventory = total_regular_gallons_daily + regular_gallons_latest_entry 

        price_per_gallon_in_inventory = (
            total_amount_in_inventory / total_regular_gallons_in_inventory
            if total_regular_gallons_in_inventory != 0
            else 0
        )

        # Insert a new entry
        self.db.current_inventory.insert_one({
            "date": date,
            "reguler_gallons": total_regular_gallons_in_inventory,
            "price_per_gallon": round(float(price_per_gallon_in_inventory),2),
            "amount": total_amount_in_inventory
        })

       self.show_message("All datewise entries synced successfully.")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = PetrolPumpApp()
    window.show()
    sys.exit(app.exec_())
