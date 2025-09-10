#include <iostream>
#include <fstream>
#include <string>
#include <iomanip>
using namespace std;

// ================= Account Base Class =================
class Account {
protected:
    int accountNumber;
    string name;
    double balance;

public:
    Account() : accountNumber(0), balance(0.0) {}

    virtual void createAccount() {
        cout << "Enter Account Number: ";
        cin >> accountNumber;
        cout << "Enter Name: ";
        cin.ignore();
        getline(cin, name);
        cout << "Enter Initial Balance: ";
        cin >> balance;
    }

    virtual void displayAccount() const {
        cout << "Account Number: " << accountNumber << endl;
        cout << "Name: " << name << endl;
        cout << "Balance: " << balance << endl;
    }

    int getAccountNumber() const { return accountNumber; }
    double getBalance() const { return balance; }
    string getName() const { return name; }

    void deposit(double amount) {
        balance += amount;
        cout << "Deposited " << amount << " successfully.\n";
    }

    bool withdraw(double amount) {
        if (amount > balance) {
            cout << "Insufficient balance!\n";
            return false;
        }
        balance -= amount;
        cout << "Withdrew " << amount << " successfully.\n";
        return true;
    }

    virtual void writeToFile(ofstream &out) const {
        out << accountNumber << "," << name << "," << balance << endl;
    }
};

// ================= Derived Class: SavingsAccount =================
class SavingsAccount : public Account {
public:
    void createAccount() override {
        cout << "Creating Savings Account...\n";
        Account::createAccount();
    }
};

// ================= Bank Management =================
class Bank {
public:
    void createAccount() {
        SavingsAccount acc;
        acc.createAccount();
        ofstream out("accounts.txt", ios::app);
        acc.writeToFile(out);
        out.close();
        cout << "Account created and saved successfully!\n";
    }

    void depositMoney() {
        int accNo;
        double amount;
        cout << "Enter Account Number: ";
        cin >> accNo;
        cout << "Enter Amount to Deposit: ";
        cin >> amount;

        updateBalance(accNo, amount, true);
    }

    void withdrawMoney() {
        int accNo;
        double amount;
        cout << "Enter Account Number: ";
        cin >> accNo;
        cout << "Enter Amount to Withdraw: ";
        cin >> amount;

        updateBalance(accNo, amount, false);
    }

    void accountStatement() {
        int accNo;
        cout << "Enter Account Number: ";
        cin >> accNo;

        ifstream in("accounts.txt");
        string line;
        bool found = false;
        while (getline(in, line)) {
            int aNo;
            string aName;
            double aBal;

            size_t pos1 = line.find(",");
            size_t pos2 = line.find_last_of(",");

            aNo = stoi(line.substr(0, pos1));
            aName = line.substr(pos1 + 1, pos2 - pos1 - 1);
            aBal = stod(line.substr(pos2 + 1));

            if (aNo == accNo) {
                cout << "=== Account Statement ===\n";
                cout << "Account Number: " << aNo << "\n";
                cout << "Name: " << aName << "\n";
                cout << "Balance: " << aBal << "\n";
                found = true;
                break;
            }
        }
        in.close();
        if (!found) cout << "Account not found!\n";
    }

private:
    void updateBalance(int accNo, double amount, bool isDeposit) {
        ifstream in("accounts.txt");
        ofstream temp("temp.txt");

        string line;
        bool found = false;

        while (getline(in, line)) {
            int aNo;
            string aName;
            double aBal;

            size_t pos1 = line.find(",");
            size_t pos2 = line.find_last_of(",");

            aNo = stoi(line.substr(0, pos1));
            aName = line.substr(pos1 + 1, pos2 - pos1 - 1);
            aBal = stod(line.substr(pos2 + 1));

            if (aNo == accNo) {
                if (isDeposit) {
                    aBal += amount;
                    cout << "Deposited successfully. New Balance: " << aBal << endl;
                } else {
                    if (amount > aBal) {
                        cout << "Insufficient balance!\n";
                    } else {
                        aBal -= amount;
                        cout << "Withdrawal successful. New Balance: " << aBal << endl;
                    }
                }
                found = true;
            }
            temp << aNo << "," << aName << "," << aBal << endl;
        }

        in.close();
        temp.close();

        remove("accounts.txt");
        rename("temp.txt", "accounts.txt");

        if (!found) cout << "Account not found!\n";
    }
};

// ================= Main Menu =================
int main() {
    Bank bank;
    int choice;

    do {
        cout << "\n=== Bank Management System ===\n";
        cout << "1. Create Account\n";
        cout << "2. Deposit Money\n";
        cout << "3. Withdraw Money\n";
        cout << "4. Account Statement\n";
        cout << "5. Exit\n";
        cout << "Enter choice: ";
        cin >> choice;

        switch (choice) {
            case 1: bank.createAccount(); break;
            case 2: bank.depositMoney(); break;
            case 3: bank.withdrawMoney(); break;
            case 4: bank.accountStatement(); break;
            case 5: cout << "Exiting...\n"; break;
            default: cout << "Invalid choice!\n";
        }
    } while (choice != 5);

    return 0;
}
