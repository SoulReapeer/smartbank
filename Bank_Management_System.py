import sys

class BankAccount:
    def __init__(self, acc_number, name, balance=0):
        self.acc_number = acc_number
        self.name = name
        self.balance = balance

    def display(self):
        print(f"\nAccount Number: {self.acc_number}")
        print(f"Account Holder: {self.name}")
        print(f"Balance: ${self.balance:.2f}")

    def deposit(self, amount):
        if amount > 0:
            self.balance += amount
            print(f"\n${amount:.2f} deposited successfully.")
        else:
            print("Invalid deposit amount.")

    def withdraw(self, amount):
        if amount <= self.balance:
            self.balance -= amount
            print(f"\n${amount:.2f} withdrawn successfully.")
        else:
            print("Insufficient balance.")

# Dictionary to hold accounts
accounts = {}

def create_account():
    acc_number = input("Enter new account number: ")
    if acc_number in accounts:
        print("Account already exists.")
        return
    name = input("Enter account holder name: ")
    initial_deposit = float(input("Enter initial deposit: "))
    accounts[acc_number] = BankAccount(acc_number, name, initial_deposit)
    print("Account created successfully!")

def view_account():
    acc_number = input("Enter account number: ")
    if acc_number in accounts:
        accounts[acc_number].display()
    else:
        print("Account not found.")

def deposit_money():
    acc_number = input("Enter account number: ")
    if acc_number in accounts:
        amount = float(input("Enter amount to deposit: "))
        accounts[acc_number].deposit(amount)
    else:
        print("Account not found.")

def withdraw_money():
    acc_number = input("Enter account number: ")
    if acc_number in accounts:
        amount = float(input("Enter amount to withdraw: "))
        accounts[acc_number].withdraw(amount)
    else:
        print("Account not found.")

def main():
    while True:
        print("\n==== Bank Management System ====")
        print("1. Create Account")
        print("2. View Account")
        print("3. Deposit Money")
        print("4. Withdraw Money")
        print("5. Exit")

        choice = input("Enter your choice (1-5): ")

        if choice == '1':
            create_account()
        elif choice == '2':
            view_account()
        elif choice == '3':
            deposit_money()
        elif choice == '4':
            withdraw_money()
        elif choice == '5':
            print("Thank you for using the Bank Management System.")
            sys.exit()
        else:
            print("Invalid choice. Try again.")

if __name__ == "__main__":
    main()
