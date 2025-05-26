#include <bits/stdc++.h>

using std::unordered_set;
using std::string;
using std::cerr;
using std::ifstream;
using std::set;
using std::istreambuf_iterator;
using std::cout;


int isKeyword(const char buffer[]) {
    const char* keywords[32] = {
        "auto", "break", "case", "char", "const", "continue", "default",
        "do", "double", "else", "enum", "extern", "float", "for", "goto",
        "if", "int", "long", "register", "return", "short", "signed",
        "sizeof", "static", "struct", "switch", "typedef", "union",
        "unsigned", "void", "volatile", "while"
    };
    for (int i = 0; i < 32; ++i) {
        if (strcmp(keywords[i], buffer) == 0)
            return 1;
    }
    return 0;
}

bool isLogicalOperator(const string& s) {
    static const unordered_set<string> logicalOps = {
        "&&", "||", "!", "<", ">", "<=", ">=", "==", "!="
    };
    return logicalOps.count(s);
}

bool isMathOperator(const string& s) {
    static const unordered_set<string> mathOps = {
        "+", "-", "*", "/", "=", "+=", "-=", "*=", "/=", "%"
    };
    return mathOps.count(s);
}

int main(int argc, char* argv[]) {
    if (argc < 2) {
        cerr << "Usage: " << argv[0] << " <input_cpp_file>\n";
        return 1;
    }

    ifstream fin(argv[1]);
    if (!fin.is_open()) {
        cerr << "Error opening file: " << argv[1] << "\n";
        return 1;
    }

    string content((istreambuf_iterator<char>(fin)), istreambuf_iterator<char>());
    fin.close();

    set<string> keywordsFound;
    set<string> identifiersFound;
    set<string> numericalValues;
    set<string> logicalOperators;
    set<string> mathOperators;
    set<char> others;

    const string otherSymbols = ",;(){}[]'\":\\&|";

    for (size_t i = 0; i < content.length(); ++i) {
        // Skip comments
        if (content[i] == '/' && i + 1 < content.length()) {
            if (content[i + 1] == '/') {
                i += 2;
                while (i < content.length() && content[i] != '\n') ++i;
                continue;
            }
            else if (content[i + 1] == '*') {
                i += 2;
                while (i + 1 < content.length() && !(content[i] == '*' && content[i + 1] == '/')) ++i;
                i += 1;
                continue;
            }
        }

        // Skip string literals
        if (content[i] == '"') {
            ++i;
            while (i < content.length() && content[i] != '"') {
                if (content[i] == '\\') ++i; // skip escaped character
                ++i;
            }
            continue;
        }

        // Check 2-character operators first
        if (i + 1 < content.length()) {
            string twoCharOp = content.substr(i, 2);
            if (isLogicalOperator(twoCharOp)) {
                logicalOperators.insert(twoCharOp);
                i++;
                continue;
            }
            if (isMathOperator(twoCharOp)) {
                mathOperators.insert(twoCharOp);
                i++;
                continue;
            }
        }

        string oneChar(1, content[i]);
        if (isLogicalOperator(oneChar)) {
            logicalOperators.insert(oneChar);
        } else if (isMathOperator(oneChar)) {
            mathOperators.insert(oneChar);
        } else if (otherSymbols.find(content[i]) != string::npos) {
            others.insert(content[i]);
        }
    }

    // Tokenize for keywords, identifiers, numbers
    string token;
    for (size_t i = 0; i <= content.length(); ++i) {
        char ch = (i < content.length()) ? content[i] : ' ';

        if (isalnum(ch) || ch == '_') {
            token += ch;
        } else {
            if (!token.empty()) {
                if (isdigit(token[0])) {
                    numericalValues.insert(token);
                } else if (isKeyword(token.c_str())) {
                    keywordsFound.insert(token);
                } else {
                    identifiersFound.insert(token);
                }
                token.clear();
            }
        }
    }

    // Output section
    auto printSet = [](const string& label, const set<string>& s) {
        cout << "----------------------------------------\n";
        cout << label << " (" << s.size() << "):\n";
        int count = 0;
        for (const auto& item : s) {
            cout << "  " << item;
            ++count;
            if (count % 8 == 0) cout << "\n";
        }
        if (count % 8 != 0) cout << "\n";
    };

    cout << "\n========== Lexical Analysis Result ==========\n";
    printSet("Keywords", keywordsFound);
    printSet("Identifiers", identifiersFound);

    cout << "----------------------------------------\n";
    cout << "Math Operators (" << mathOperators.size() << "):\n";
    int count = 0;
    for (const auto& op : mathOperators) {
        cout << "  " << op;
        ++count;
        if (count % 8 == 0) cout << "\n";
    }
    if (count % 8 != 0) cout << "\n";

    cout << "----------------------------------------\n";
    cout << "Logical Operators (" << logicalOperators.size() << "):\n";
    count = 0;
    for (const auto& op : logicalOperators) {
        cout << "  " << op;
        ++count;
        if (count % 8 == 0) cout << "\n";
    }
    if (count % 8 != 0) cout << "\n";

    printSet("Numerical Values", numericalValues);

    cout << "----------------------------------------\n";
    cout << "Others (" << others.size() << "):\n";
    count = 0;
    for (const auto& ch : others) {
        cout << "  " << ch;
        ++count;
        if (count % 16 == 0) cout << "\n";
    }
    if (count % 16 != 0) cout << "\n";
    cout << "========================================\n";

    return 0;
}
