from pymongo import MongoClient

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['inventory']  # Replace 'inventory' with your desired database name
collection = db['items']  # Create a collection named 'items'

def add_item(name, quantity):
    item = {'name': name, 'quantity': quantity}
    collection.insert_one(item)

def purchase_item(name, quantity):
    # Validate that the quantity is greater than 0
    if quantity <= 0:
        print("Error: Quantity must be greater than 0.")
        return

    # Update the item only if the current quantity is greater than 0
    result = collection.update_one(
        {'name': name, 'quantity': {'$gt': 0}},
        {'$inc': {'quantity': quantity}}
    )

    if result.modified_count == 0:
        print("Error: Not enough quantity to purchase.")

def sell_item(name, quantity):
    # Validate that the quantity is greater than 0
    if quantity <= 0:
        print("Error: Quantity must be greater than 0.")
        return

    # Update the item only if the current quantity is greater than the selling quantity
    result = collection.update_one(
        {'name': name, 'quantity': {'$gt': quantity}},
        {'$inc': {'quantity': -quantity}}
    )

    if result.modified_count == 0:
        print("Error: Not enough quantity to sell.")
def get_inventory():
    # Retrieve all items in the inventory
    return list(collection.find())

def main():
    while True:
        print("\nOptions:")
        print("1. Add item")
        print("2. Sell item")
        print("3. Purchase item")
        print("4. View inventory")
        print("5. Exit")

        choice = input("Enter your choice (1-5): ")

        if choice == '1':
            name = input("Enter the item name: ")
            quantity = int(input("Enter the quantity: "))
            add_item(name, quantity)
            print(f"{quantity} {name}(s) added to the inventory.")
        elif choice == '2':
            name = input("Enter the item name to sell: ")
            quantity = int(input("Enter the quantity to sell: "))
            sell_item(name, quantity)
            print(f"{quantity} {name}(s) sold.")
        elif choice == '3':
            name = input("Enter the item name to purchase: ")
            quantity = int(input("Enter the quantity to purchase: "))
            purchase_item(name, quantity)
            print(f"{quantity} {name}(s) purchased.")
        elif choice == '4':
            print("\nCurrent Inventory:")
            for item in get_inventory():
                print(f"{item['name']}: {item['quantity']}")
        elif choice == '5':
            print("Exiting the inventory management system. Goodbye!")
            break
        else:
            print("Invalid choice. Please enter a number between 1 and 5.")

if __name__ == "__main__":
    main()