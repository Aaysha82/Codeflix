/*
DETECTION/structuring.cpp
C++ OOP Rule-based AML Detection Engine
Compile: g++ -o DETECTION/detector DETECTION/structuring.cpp -std=c++17
Run:     DETECTION/detector <json_input>
*/
#include <iostream>
#include <string>
#include <vector>
#include <sstream>
#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <cstdio>

#include <iostream>
#include <string>
#include <vector>
#include <sstream>
#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <cstdio>
#include <map>

// Lightweight Manual JSON Parser for simple flat objects
class SimpleJSON {
private:
    std::string raw;
    std::map<std::string, std::string> data;

    std::string trim(const std::string& s) {
        size_t first = s.find_first_not_of(" \"\n\r\t");
        if (first == std::string::npos) return "";
        size_t last = s.find_last_not_of(" \"\n\r\t");
        return s.substr(first, (last - first + 1));
    }

public:
    SimpleJSON(const std::string& json_str) : raw(json_str) {
        parse();
    }

    void parse() {
        size_t start = raw.find('{');
        size_t end = raw.find_last_of('}');
        if (start == std::string::npos || end == std::string::npos) return;
        
        std::string content = raw.substr(start + 1, end - start - 1);
        
        bool in_quotes = false;
        std::string current_item;
        for (char c : content) {
            if (c == '\"') in_quotes = !in_quotes;
            if (c == ',' && !in_quotes) {
                process_item(current_item);
                current_item = "";
            } else {
                current_item += c;
            }
        }
        process_item(current_item);
    }

    void process_item(const std::string& item) {
        size_t colon = item.find(':');
        if (colon != std::string::npos) {
            std::string key = trim(item.substr(0, colon));
            std::string val = trim(item.substr(colon + 1));
            data[key] = val;
        }
    }

    std::string value(const std::string& key, const std::string& def) const {
        auto it = data.find(key);
        return (it != data.end()) ? it->second : def;
    }

    double value_double(const std::string& key, double def) const {
        auto it = data.find(key);
        return (it != data.end()) ? std::atof(it->second.c_str()) : def;
    }

    int value_int(const std::string& key, int def) const {
        auto it = data.find(key);
        return (it != data.end()) ? std::atoi(it->second.c_str()) : def;
    }
    
    std::string dump_result(bool flagged, double score, const std::vector<std::string>& rules, const std::vector<std::string>& explanations) const {
        std::stringstream ss;
        ss << "{\"is_flagged\":" << (flagged ? "true" : "false") << ",";
        ss << "\"risk_score\":" << score << ",";
        ss << "\"triggered_rules\":[";
        for (size_t i = 0; i < rules.size(); ++i) {
            ss << "\"" << rules[i] << "\"" << (i == rules.size() - 1 ? "" : ",");
        }
        ss << "],\"explanations\":[";
        for (size_t i = 0; i < explanations.size(); ++i) {
            ss << "\"" << explanations[i] << "\"" << (i == explanations.size() - 1 ? "" : ",");
        }
        ss << "]}";
        return ss.str();
    }
};

// ============================================================
// BASE CLASS: Transaction
// ============================================================
class Transaction {
protected:
    std::string transaction_id;
    std::string account_id;
    double amount;
    std::string location;
    std::string channel;
    std::string currency;
    int hour;
    int is_weekend;

public:
    Transaction(const SimpleJSON& j) {
        transaction_id = j.value("transaction_id", "txn_000");
        account_id     = j.value("account_id", "acc_000");
        amount         = j.value_double("amount", 0.0);
        location       = j.value("location", "Mumbai");
        channel        = j.value("channel", "Online");
        currency       = j.value("currency", "INR");
        hour           = j.value_int("hour", 12);
        is_weekend     = j.value_int("is_weekend", 0);
    }

    virtual ~Transaction() = default;

    // Getters
    double getAmount() const { return amount; }
    std::string getLocation() const { return location; }
    std::string getChannel() const { return channel; }
    std::string getCurrency() const { return currency; }
    std::string getAccountId() const { return account_id; }
    std::string getTxnId() const { return transaction_id; }
    int getHour() const { return hour; }
    int getIsWeekend() const { return is_weekend; }
};

// ============================================================
// INTERFACE: RuleDetector (Pure Abstract)
// ============================================================
class RuleDetector {
public:
    virtual ~RuleDetector() = default;
    virtual bool detect(const Transaction& txn) const = 0;
    virtual double getRiskScore(const Transaction& txn) const = 0;
    virtual std::string getRuleName() const = 0;
    virtual std::string getExplanation(const Transaction& txn) const = 0;
};

// ============================================================
// RULE 1: Structuring Detection
// ============================================================
class StructuringDetector : public RuleDetector {
private:
    static constexpr double THRESHOLD = 1000000.0;
    static constexpr double LOWER_BOUND_RATIO = 0.80;
    static constexpr double UPPER_BOUND_RATIO = 0.99;

public:
    bool detect(const Transaction& txn) const override {
        double amt = txn.getAmount();
        return (amt >= THRESHOLD * LOWER_BOUND_RATIO && amt <= THRESHOLD * UPPER_BOUND_RATIO);
    }

    double getRiskScore(const Transaction& txn) const override {
        if (!detect(txn)) return 0.0;
        return 0.65 + (txn.getAmount() / THRESHOLD - 0.80) / 0.20 * 0.30;
    }

    std::string getRuleName() const override { return "STRUCTURING"; }

    std::string getExplanation(const Transaction& txn) const override {
        if (!detect(txn)) return "";
        char buf[256];
        snprintf(buf, sizeof(buf),
            "Amount INR %.2f is %.1f%% of the 10L threshold (Structuring)",
            txn.getAmount(), (txn.getAmount() / THRESHOLD) * 100.0
        );
        return std::string(buf);
    }
};

// ============================================================
// RULE 2: Layering Detection
// ============================================================
class LayeringDetector : public RuleDetector {
private:
    static constexpr double HIGH_VALUE_THRESHOLD = 500000.0;
    const std::vector<std::string> HR_LOCS = {"Cayman Islands", "Panama", "Dubai", "Switzerland"};
    const std::vector<std::string> HR_CHANS = {"Wire Transfer", "RTGS", "SWIFT"};

    bool isHR(const std::vector<std::string>& list, const std::string& val) const {
        return std::find(list.begin(), list.end(), val) != list.end();
    }

public:
    bool detect(const Transaction& txn) const override {
        int hits = (txn.getAmount() >= HIGH_VALUE_THRESHOLD) +
                   isHR(HR_LOCS, txn.getLocation()) +
                   isHR(HR_CHANS, txn.getChannel());
        return hits >= 2;
    }

    double getRiskScore(const Transaction& txn) const override {
        if (!detect(txn)) return 0.0;
        return std::min(0.95, 0.60 + (txn.getAmount() >= HIGH_VALUE_THRESHOLD ? 0.35 : 0.15));
    }

    std::string getRuleName() const override { return "LAYERING"; }
    std::string getExplanation(const Transaction& txn) const override {
        return "High-value cross-border layering indicators detected.";
    }
};

// ============================================================
// RULE 3: Smurfing Detection
// ============================================================
class SmurfingDetector : public RuleDetector {
public:
    bool detect(const Transaction& txn) const override {
        return (txn.getAmount() >= 1000 && txn.getAmount() <= 50000) &&
               (txn.getHour() < 5 || txn.getIsWeekend());
    }
    double getRiskScore(const Transaction& txn) const override {
        return detect(txn) ? 0.75 : 0.0;
    }
    std::string getRuleName() const override { return "SMURFING"; }
    std::string getExplanation(const Transaction& txn) const override {
        return "Anomalous small transaction timing suggests smurfing.";
    }
};

// ============================================================
// ENGINE
// ============================================================
class AMLDetectionEngine {
private:
    std::vector<RuleDetector*> rules;
public:
    AMLDetectionEngine() {
        rules.push_back(new StructuringDetector());
        rules.push_back(new LayeringDetector());
        rules.push_back(new SmurfingDetector());
    }
    ~AMLDetectionEngine() { for (auto* r : rules) delete r; }

    std::string analyze(const Transaction& txn) const {
        bool flagged = false;
        double risk_score = 0.0;
        std::vector<std::string> triggered;
        std::vector<std::string> explanations;

        for (const auto* rule : rules) {
            if (rule->detect(txn)) {
                flagged = true;
                double score = rule->getRiskScore(txn);
                if (score > risk_score) risk_score = score;
                triggered.push_back(rule->getRuleName());
                explanations.push_back(rule->getExplanation(txn));
            }
        }
        
        SimpleJSON sj(""); // dummy for helper access
        return sj.dump_result(flagged, risk_score, triggered, explanations);
    }
};

int main(int argc, char* argv[]) {
    try {
        std::string input;
        if (argc > 1) input = argv[1];
        else std::getline(std::cin, input);

        SimpleJSON j(input);
        Transaction txn(j);
        AMLDetectionEngine engine;
        
        std::cout << engine.analyze(txn) << std::endl;
    } catch (const std::exception& e) {
        std::cout << "{\"error\":\"" << e.what() << "\",\"is_flagged\":false,\"risk_score\":0.0}" << std::endl;
    }
    return 0;
}

