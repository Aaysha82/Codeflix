"""
DETECTION/structuring.cpp
C++ OOP Rule-based AML Detection Engine
Compile: g++ -o DETECTION/detector DETECTION/structuring.cpp -std=c++17
Run:     DETECTION/detector <json_input>
"""
#include <iostream>
#include <string>
#include <vector>
#include <sstream>
#include <algorithm>
#include <cmath>
#include <cstdlib>

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
    Transaction(
        const std::string& tid, const std::string& acc,
        double amt, const std::string& loc,
        const std::string& ch, const std::string& cur,
        int hr, int weekend
    ) : transaction_id(tid), account_id(acc), amount(amt),
        location(loc), channel(ch), currency(cur),
        hour(hr), is_weekend(weekend) {}

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

    virtual std::string getType() const { return "base"; }
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
// Structuring: transactions just below 10 lakh reporting threshold
// ============================================================
class StructuringDetector : public RuleDetector {
private:
    static constexpr double THRESHOLD = 1000000.0; // INR 10 lakh
    static constexpr double LOWER_BOUND_RATIO = 0.80;
    static constexpr double UPPER_BOUND_RATIO = 0.99;

public:
    bool detect(const Transaction& txn) const override {
        double amt = txn.getAmount();
        double lower = THRESHOLD * LOWER_BOUND_RATIO;
        double upper = THRESHOLD * UPPER_BOUND_RATIO;
        return (amt >= lower && amt <= upper);
    }

    double getRiskScore(const Transaction& txn) const override {
        if (!detect(txn)) return 0.0;
        double amt = txn.getAmount();
        double ratio = amt / THRESHOLD;
        // Closer to threshold = higher risk (0.65–0.95 range)
        return 0.65 + (ratio - 0.80) / 0.20 * 0.30;
    }

    std::string getRuleName() const override { return "STRUCTURING"; }

    std::string getExplanation(const Transaction& txn) const override {
        if (!detect(txn)) return "";
        char buf[256];
        snprintf(buf, sizeof(buf),
            "Transaction amount INR %.2f is %.1f%% of the 10L reporting threshold — classic structuring pattern",
            txn.getAmount(), (txn.getAmount() / THRESHOLD) * 100.0
        );
        return std::string(buf);
    }
};

// ============================================================
// RULE 2: Layering Detection
// Layering: large amounts to high-risk jurisdictions via wire
// ============================================================
class LayeringDetector : public RuleDetector {
private:
    static constexpr double HIGH_VALUE_THRESHOLD = 500000.0;
    const std::vector<std::string> HIGH_RISK_LOCATIONS = {
        "Cayman Islands", "Panama", "Switzerland", "Dubai",
        "British Virgin Islands", "Malta", "Isle of Man"
    };
    const std::vector<std::string> HIGH_RISK_CHANNELS = {
        "Wire Transfer", "RTGS", "SWIFT"
    };
    const std::vector<std::string> FOREIGN_CURRENCIES = {
        "USD", "EUR", "CHF", "AED", "GBP", "SGD"
    };

    bool isHighRiskLocation(const std::string& loc) const {
        return std::find(HIGH_RISK_LOCATIONS.begin(), HIGH_RISK_LOCATIONS.end(), loc)
               != HIGH_RISK_LOCATIONS.end();
    }

    bool isHighRiskChannel(const std::string& ch) const {
        return std::find(HIGH_RISK_CHANNELS.begin(), HIGH_RISK_CHANNELS.end(), ch)
               != HIGH_RISK_CHANNELS.end();
    }

    bool isForeignCurrency(const std::string& cur) const {
        return std::find(FOREIGN_CURRENCIES.begin(), FOREIGN_CURRENCIES.end(), cur)
               != FOREIGN_CURRENCIES.end();
    }

public:
    bool detect(const Transaction& txn) const override {
        bool highVal = txn.getAmount() >= HIGH_VALUE_THRESHOLD;
        bool highRiskLoc = isHighRiskLocation(txn.getLocation());
        bool highRiskCh = isHighRiskChannel(txn.getChannel());
        bool foreignCur = isForeignCurrency(txn.getCurrency());

        // Flag if 2+ layering indicators present
        int score = (int)highVal + (int)highRiskLoc + (int)highRiskCh + (int)foreignCur;
        return score >= 2;
    }

    double getRiskScore(const Transaction& txn) const override {
        if (!detect(txn)) return 0.0;
        bool highVal = txn.getAmount() >= HIGH_VALUE_THRESHOLD;
        bool highRiskLoc = isHighRiskLocation(txn.getLocation());
        bool highRiskCh = isHighRiskChannel(txn.getChannel());
        bool foreignCur = isForeignCurrency(txn.getCurrency());
        int indicators = (int)highVal + (int)highRiskLoc + (int)highRiskCh + (int)foreignCur;
        // 2 indicators = 0.70, 3 = 0.82, 4 = 0.95
        return std::min(0.95, 0.55 + indicators * 0.10);
    }

    std::string getRuleName() const override { return "LAYERING"; }

    std::string getExplanation(const Transaction& txn) const override {
        if (!detect(txn)) return "";
        return "High-value transaction via wire transfer to high-risk jurisdiction — "
               "matches layering pattern for money laundering";
    }
};

// ============================================================
// RULE 3: Smurfing Detection
// Smurfing: rapid small transactions from multiple sources
// ============================================================
class SmurfingDetector : public RuleDetector {
private:
    static constexpr double SMALL_TXN_MAX = 50000.0;
    static constexpr double SMALL_TXN_MIN = 1000.0;
    static constexpr int ODD_HOUR_START = 0;
    static constexpr int ODD_HOUR_END = 5;

    bool isOddHour(int hour) const {
        return (hour >= ODD_HOUR_START && hour <= ODD_HOUR_END);
    }

public:
    bool detect(const Transaction& txn) const override {
        bool smallAmt = (txn.getAmount() >= SMALL_TXN_MIN && txn.getAmount() <= SMALL_TXN_MAX);
        bool oddHour = isOddHour(txn.getHour());
        bool weekend = txn.getIsWeekend() == 1;
        // Small amounts at odd hours or weekends suggest smurfing
        return smallAmt && (oddHour || weekend);
    }

    double getRiskScore(const Transaction& txn) const override {
        if (!detect(txn)) return 0.0;
        double base = 0.60;
        if (isOddHour(txn.getHour())) base += 0.10;
        if (txn.getIsWeekend() == 1) base += 0.05;
        return std::min(base, 0.90);
    }

    std::string getRuleName() const override { return "SMURFING"; }

    std::string getExplanation(const Transaction& txn) const override {
        if (!detect(txn)) return "";
        char buf[256];
        snprintf(buf, sizeof(buf),
            "Small transaction of INR %.2f at hour %d — consistent with smurfing/structuring pattern",
            txn.getAmount(), txn.getHour()
        );
        return std::string(buf);
    }
};

// ============================================================
// COMPOSITE: AML Detection Engine
// Polymorphic — runs all rules
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

    ~AMLDetectionEngine() {
        for (auto* r : rules) delete r;
    }

    struct DetectionResult {
        bool is_flagged;
        double max_risk_score;
        std::vector<std::string> triggered_rules;
        std::vector<std::string> explanations;
    };

    DetectionResult analyze(const Transaction& txn) const {
        DetectionResult result;
        result.is_flagged = false;
        result.max_risk_score = 0.0;

        for (const auto* rule : rules) {
            if (rule->detect(txn)) {
                result.is_flagged = true;
                double score = rule->getRiskScore(txn);
                if (score > result.max_risk_score) result.max_risk_score = score;
                result.triggered_rules.push_back(rule->getRuleName());
                result.explanations.push_back(rule->getExplanation(txn));
            }
        }
        return result;
    }
};

// ============================================================
// JSON HELPERS
// ============================================================
std::string jsonEscape(const std::string& s) {
    std::string out;
    for (char c : s) {
        if (c == '"') out += "\\\"";
        else if (c == '\\') out += "\\\\";
        else if (c == '\n') out += "\\n";
        else out += c;
    }
    return out;
}

std::string extractJsonString(const std::string& json, const std::string& key) {
    std::string search = "\"" + key + "\"";
    size_t pos = json.find(search);
    if (pos == std::string::npos) return "";
    pos = json.find("\"", pos + search.size() + 1);
    if (pos == std::string::npos) return "";
    size_t end = json.find("\"", pos + 1);
    while (end != std::string::npos && json[end - 1] == '\\') end = json.find("\"", end + 1);
    if (end == std::string::npos) return "";
    return json.substr(pos + 1, end - pos - 1);
}

double extractJsonDouble(const std::string& json, const std::string& key) {
    std::string search = "\"" + key + "\"";
    size_t pos = json.find(search);
    if (pos == std::string::npos) return 0.0;
    pos = json.find(":", pos + search.size());
    if (pos == std::string::npos) return 0.0;
    pos++;
    while (pos < json.size() && (json[pos] == ' ' || json[pos] == '\t')) pos++;
    return std::stod(json.substr(pos));
}

int extractJsonInt(const std::string& json, const std::string& key) {
    return (int)extractJsonDouble(json, key);
}

// ============================================================
// MAIN ENTRY POINT
// Input: JSON string as first argument
// Output: JSON result to stdout
// ============================================================
int main(int argc, char* argv[]) {
    std::string input;
    if (argc > 1) {
        input = argv[1];
    } else {
        // Read from stdin
        std::getline(std::cin, input);
    }

    // Parse input JSON
    std::string tid = extractJsonString(input, "transaction_id");
    std::string acc = extractJsonString(input, "account_id");
    double amount = extractJsonDouble(input, "amount");
    std::string loc = extractJsonString(input, "location");
    std::string ch = extractJsonString(input, "channel");
    std::string cur = extractJsonString(input, "currency");
    int hr = extractJsonInt(input, "hour");
    int weekend = extractJsonInt(input, "is_weekend");

    Transaction txn(tid, acc, amount, loc, ch, cur, hr, weekend);
    AMLDetectionEngine engine;
    auto result = engine.analyze(txn);

    // Build JSON output
    std::ostringstream out;
    out << "{";
    out << "\"is_flagged\":" << (result.is_flagged ? "true" : "false") << ",";
    out << "\"risk_score\":" << result.max_risk_score << ",";
    out << "\"triggered_rules\":[";
    for (size_t i = 0; i < result.triggered_rules.size(); i++) {
        out << "\"" << jsonEscape(result.triggered_rules[i]) << "\"";
        if (i + 1 < result.triggered_rules.size()) out << ",";
    }
    out << "],";
    out << "\"explanations\":[";
    for (size_t i = 0; i < result.explanations.size(); i++) {
        out << "\"" << jsonEscape(result.explanations[i]) << "\"";
        if (i + 1 < result.explanations.size()) out << ",";
    }
    out << "]";
    out << "}";

    std::cout << out.str() << std::endl;
    return 0;
}
