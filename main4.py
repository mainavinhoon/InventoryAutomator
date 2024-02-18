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
        unique_dates = self.db.daily_report.distinct("date")

        for date in unique_dates:
            # Get the latest daily report for the current date
            latest_daily_report = self.db.daily_report.find({"date": date}).sort("date", -1).limit(1).next()

            # Get the latest purchase for the current date
            latest_purchase = self.db.purchases.find({"date": date}).sort("date", -1).limit(1).next() if self.db.purchases.count_documents({"date": date}) > 0 else None

            # Calculate the sum of reguler_gallons and amount for all purchase entries
            total_reguler_gallons_purchase = sum(float(entry["reguler_gallons"]) for entry in self.db.purchases.find({"date": date}))
            total_amount_purchase = sum(float(entry["amount"]) for entry in self.db.purchases.find({"date": date}))


            try:
                # Get the entry for the previous date
                previous_date = self.db.daily_report.find({"date": {"$lt": date}}).sort("date", -1).limit(1).next()
                previous_entry = self.db.current_inventory.find({"date": previous_date["date"]}).sort("date", -1).limit(1).next() if self.db.current_inventory.count_documents({"date": previous_date["date"]}) > 0 else None

                if previous_entry:
                    # Use the values from the previous entry
                    regular_gallons_previous_entry = round(float(previous_entry["reguler_gallons"]), 2)
                    # price_per_gallon_previous_entry = round(float(previous_entry["price_per_gallon"]), 2)
                    amount_previous_entry = round(float(previous_entry["amount"]), 2)
                else:
                    # Set default values if no previous entry exists
                    regular_gallons_previous_entry = 0
                    # price_per_gallon_previous_entry = 0
                    amount_previous_entry = 0

            except StopIteration:
                # Handle the case where no previous date is found
                regular_gallons_previous_entry = 0
                # price_per_gallon_previous_entry = 0
                amount_previous_entry = 0

            # Check if an entry for the date already exists in current_inventory
            existing_entry = self.db.current_inventory.find_one({"date": date})

            if existing_entry:
                # Update the existing entry for the current date
                total_regular_gallons_daily = round(float(total_reguler_gallons_purchase), 2) - round(float(latest_daily_report["reguler_gallons"]), 2)
                # total_amount_purchases = round(float(latest_purchase["amount"]), 2)
                total_amount_in_inventory = amount_previous_entry + total_amount_purchase
                total_regular_gallons_in_inventory = total_regular_gallons_daily + regular_gallons_previous_entry

                price_per_gallon_in_inventory = (
                    total_amount_in_inventory / total_regular_gallons_in_inventory
                    if total_regular_gallons_in_inventory != 0
                    else 0
                )

                # Update all details in the existing entry
                self.db.current_inventory.update_one(
                    {"date": date},
                    {
                        "$set": {
                            "reguler_gallons": total_regular_gallons_in_inventory,
                            "price_per_gallon": round(float(price_per_gallon_in_inventory), 2),
                            "amount": total_amount_in_inventory
                        }
                    }
                )
            else:
                # Insert a new entry if it doesn't exist
                total_regular_gallons_daily = round(float(latest_purchase["reguler_gallons"]), 2) - round(float(latest_daily_report["reguler_gallons"]), 2)
                # total_amount_purchases = round(float(latest_purchase["amount"]), 2)
                total_amount_in_inventory = amount_previous_entry + total_amount_purchase
                total_regular_gallons_in_inventory = total_regular_gallons_daily + regular_gallons_previous_entry

                price_per_gallon_in_inventory = (
                    total_amount_in_inventory / total_regular_gallons_in_inventory
                    if total_regular_gallons_in_inventory != 0
                    else 0
                )

                # Insert a new entry
                self.db.current_inventory.insert_one({
                    "date": date,
                    "reguler_gallons": total_regular_gallons_in_inventory,
                    "price_per_gallon": round(float(price_per_gallon_in_inventory), 2),
                    "amount": total_amount_in_inventory
                })

        self.show_message("All datewise entries synced successfully.")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = PetrolPumpApp()
    window.show()
    sys.exit(app.exec_())
