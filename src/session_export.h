#pragma once

#ifdef _WIN32
#include <windows.h>
#endif

#include <algorithm>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <optional>
#include <sstream>
#include <string>
#include <vector>

namespace session_export {

struct Record {
    std::string id;
    std::string label;
    std::string startIso;
    std::string endIso;
    int units{0};
    std::optional<int> legacyPeakToTroughDrawdown;
    std::optional<int> highWaterUnits;
    std::string source;
    std::optional<std::uint64_t> activeDurationMs;
    std::optional<int> bankrollLowUnits;
    std::optional<std::int64_t> startBalanceMinor;
    std::optional<std::int64_t> endBalanceMinor;
    std::string balanceCurrency;
    // v21.2.87: exact session P/L in 1/100 strategy unit. Older session files
    // only stored integer units; units remains for backwards compatibility.
    std::optional<int> unitsHundredths;
    // v21.2.90: counterfactual strategy models. These are intentionally
    // independent of the live GesamtEV filter button so the workbook can
    // compare both policies over the same observed betting opportunities.
    std::optional<int> minEdgeModelUnitsHundredths;
    std::optional<int> positiveCombinedEvModelUnitsHundredths;
    std::optional<int> minEdgeModelSignals;
    std::optional<int> positiveCombinedEvModelSignals;
    std::optional<bool> combinedEvFilterEnabledAtSave;
    // v21.2.110: configured threshold policy, sampled at each signal.
    // Absent for old sessions; zero is a known result, not missing data.
    std::optional<int> configuredCombinedEvModelUnitsHundredths;
    std::optional<int> configuredCombinedEvModelSignals;
    std::optional<double> combinedMinEdgeUsedMinimum;
    std::optional<double> combinedMinEdgeUsedMaximum;
    // v21.2.113: active signal policy frozen at betsopen; independent of chips.
    // Missing for older sessions, never retroactively interpreted as zero.
    std::optional<int> activePaperPairHundredths;
    std::optional<int> activePaperMainHundredths;
    std::optional<int> activePaperSignals;
    std::optional<int> confirmedActualHundredths;

};

inline std::string XmlEscape(const std::string& text) {
    std::string out;
    out.reserve(text.size() + 16);
    for (char ch : text) {
        const unsigned char byte = static_cast<unsigned char>(ch);
        // XML 1.0 does not permit the remaining C0 control characters.
        // Keep TAB/LF/CR, discard invalid controls before writing the package.
        if (byte < 0x20 && ch != '\t' && ch != '\n' && ch != '\r') continue;
        switch (ch) {
            case '&': out += "&amp;"; break;
            case '<': out += "&lt;"; break;
            case '>': out += "&gt;"; break;
            case '\"': out += "&quot;"; break;
            case '\'': out += "&apos;"; break;
            default: out.push_back(ch); break;
        }
    }
    return out;
}

inline bool ReplaceFileAtomically(const std::filesystem::path& source,
                                  const std::filesystem::path& target);

inline std::vector<Record> HistoricalRecords() {
    // The pre-v117 sample sessions mixed the former Pair-only unit definition
    // with sessions requiring a main bet. A fresh history must stay empty until
    // a real session record is saved.
    return {};
}

inline bool WriteRecordFile(const std::filesystem::path& directory,
                            const Record& record,
                            std::wstring& error) {
    std::error_code ec;
    std::filesystem::create_directories(directory, ec);
    if (ec) {
        error = L"Session-Ordner konnte nicht angelegt werden.";
        return false;
    }
    const auto finalPath = directory / (record.id + ".session");
    const auto tempPath = directory / (record.id + ".session.tmp");
    {
        std::ofstream out(tempPath, std::ios::binary | std::ios::trunc);
        if (!out) {
            error = L"Session-Datensatz konnte nicht geschrieben werden.";
            return false;
        }
        out << "BaccaratCounterSession 7\n"
            << std::quoted(record.id) << '\n'
            << std::quoted(record.label) << '\n'
            << std::quoted(record.startIso) << '\n'
            << std::quoted(record.endIso) << '\n'
            << record.units << '\n'
            << (record.legacyPeakToTroughDrawdown.has_value() ? 1 : 0) << ' '
            << record.legacyPeakToTroughDrawdown.value_or(0) << '\n'
            << (record.highWaterUnits.has_value() ? 1 : 0) << ' '
            << record.highWaterUnits.value_or(0) << '\n'
            << std::quoted(record.source) << '\n'
            << (record.activeDurationMs.has_value() ? 1 : 0) << ' '
            << record.activeDurationMs.value_or(0) << '\n'
            << (record.bankrollLowUnits.has_value() ? 1 : 0) << ' '
            << record.bankrollLowUnits.value_or(0) << '\n'
            << (record.startBalanceMinor.has_value() ? 1 : 0) << ' '
            << record.startBalanceMinor.value_or(0) << '\n'
            << (record.endBalanceMinor.has_value() ? 1 : 0) << ' '
            << record.endBalanceMinor.value_or(0) << '\n'
            << std::quoted(record.balanceCurrency) << '\n'
            << (record.unitsHundredths.has_value() ? 1 : 0) << ' '
            << record.unitsHundredths.value_or(0) << '\n'
            << (record.minEdgeModelUnitsHundredths.has_value() ? 1 : 0) << ' '
            << record.minEdgeModelUnitsHundredths.value_or(0) << '\n'
            << (record.positiveCombinedEvModelUnitsHundredths.has_value() ? 1 : 0) << ' '
            << record.positiveCombinedEvModelUnitsHundredths.value_or(0) << '\n'
            << (record.minEdgeModelSignals.has_value() ? 1 : 0) << ' '
            << record.minEdgeModelSignals.value_or(0) << '\n'
            << (record.positiveCombinedEvModelSignals.has_value() ? 1 : 0) << ' '
            << record.positiveCombinedEvModelSignals.value_or(0) << '\n'
            << (record.combinedEvFilterEnabledAtSave.has_value() ? 1 : 0) << ' '
            << (record.combinedEvFilterEnabledAtSave.value_or(false) ? 1 : 0) << '\n'
            << (record.configuredCombinedEvModelUnitsHundredths.has_value() ? 1 : 0) << ' '
            << record.configuredCombinedEvModelUnitsHundredths.value_or(0) << '\n'
            << (record.configuredCombinedEvModelSignals.has_value() ? 1 : 0) << ' '
            << record.configuredCombinedEvModelSignals.value_or(0) << '\n'
            << std::setprecision(17)
            << (record.combinedMinEdgeUsedMinimum.has_value() ? 1 : 0) << ' '
            << record.combinedMinEdgeUsedMinimum.value_or(0) << '\n'
            << (record.combinedMinEdgeUsedMaximum.has_value() ? 1 : 0) << ' '
            << record.combinedMinEdgeUsedMaximum.value_or(0) << '\n'
            << (record.activePaperPairHundredths.has_value() ? 1 : 0) << ' '
            << record.activePaperPairHundredths.value_or(0) << '\n'
            << (record.activePaperMainHundredths.has_value() ? 1 : 0) << ' '
            << record.activePaperMainHundredths.value_or(0) << '\n'
            << (record.activePaperSignals.has_value() ? 1 : 0) << ' '
            << record.activePaperSignals.value_or(0) << '\n'
            << (record.confirmedActualHundredths.has_value() ? 1 : 0) << ' '
            << record.confirmedActualHundredths.value_or(0) << '\n';

        out.flush();
        if (!out) {
            error = L"Session-Datensatz konnte nicht vollständig geschrieben werden.";
            return false;
        }
    }
    if (!ReplaceFileAtomically(tempPath, finalPath)) {
        std::filesystem::remove(tempPath, ec);
        error = L"Session-Datensatz konnte nicht atomar aktualisiert werden.";
        return false;
    }
    return true;
}

inline std::optional<Record> ReadRecordFile(const std::filesystem::path& path) {
    std::ifstream in(path, std::ios::binary);
    if (!in) return std::nullopt;
    std::string magic;
    int version = 0;
    if (!(in >> magic >> version) || magic != "BaccaratCounterSession" ||
        (version != 1 && version != 2 && version != 3 && version != 4 && version != 5 && version != 6 && version != 7)) return std::nullopt;
    Record record;
    int hasLegacy = 0, legacy = 0, hasPeak = 0, peak = 0;
    if (!(in >> std::quoted(record.id)
             >> std::quoted(record.label)
             >> std::quoted(record.startIso)
             >> std::quoted(record.endIso)
             >> record.units
             >> hasLegacy >> legacy
             >> hasPeak >> peak
             >> std::quoted(record.source))) return std::nullopt;
    if (hasLegacy) record.legacyPeakToTroughDrawdown = legacy;
    if (hasPeak) record.highWaterUnits = peak;
    if (version >= 2) {
        int hasDuration = 0, hasLow = 0, low = 0;
        std::uint64_t duration = 0;
        if (!(in >> hasDuration >> duration >> hasLow >> low)) return std::nullopt;
        if (hasDuration) record.activeDurationMs = duration;
        if (hasLow) record.bankrollLowUnits = low;
    }
    if (version >= 3) {
        int hasStartBalance = 0, hasEndBalance = 0;
        std::int64_t startBalance = 0, endBalance = 0;
        if (!(in >> hasStartBalance >> startBalance
                 >> hasEndBalance >> endBalance
                 >> std::quoted(record.balanceCurrency))) return std::nullopt;
        if (hasStartBalance) record.startBalanceMinor = startBalance;
        if (hasEndBalance) record.endBalanceMinor = endBalance;
    }
    if (version >= 4) {
        int hasExactUnits = 0, exactUnitsHundredths = 0;
        if (!(in >> hasExactUnits >> exactUnitsHundredths)) return std::nullopt;
        if (hasExactUnits) record.unitsHundredths = exactUnitsHundredths;
    }
    if (version >= 5) {
        int hasMinEdgeModel = 0, minEdgeModel = 0;
        int hasPositiveModel = 0, positiveModel = 0;
        int hasMinEdgeSignals = 0, minEdgeSignals = 0;
        int hasPositiveSignals = 0, positiveSignals = 0;
        int hasFilterState = 0, filterState = 0;
        if (!(in >> hasMinEdgeModel >> minEdgeModel
                 >> hasPositiveModel >> positiveModel
                 >> hasMinEdgeSignals >> minEdgeSignals
                 >> hasPositiveSignals >> positiveSignals
                 >> hasFilterState >> filterState)) return std::nullopt;
        if (hasMinEdgeModel) record.minEdgeModelUnitsHundredths = minEdgeModel;
        if (hasPositiveModel) record.positiveCombinedEvModelUnitsHundredths = positiveModel;
        if (hasMinEdgeSignals) record.minEdgeModelSignals = minEdgeSignals;
        if (hasPositiveSignals) record.positiveCombinedEvModelSignals = positiveSignals;
        if (hasFilterState) record.combinedEvFilterEnabledAtSave = filterState != 0;
    }
    if (version >= 6) {
        int hasModel = 0, model = 0, hasSignals = 0, signals = 0;
        int hasMinimum = 0, hasMaximum = 0;
        double minimum = 0, maximum = 0;
        if (!(in >> hasModel >> model >> hasSignals >> signals
                 >> hasMinimum >> minimum >> hasMaximum >> maximum)) return std::nullopt;
        if (hasModel) record.configuredCombinedEvModelUnitsHundredths = model;
        if (hasSignals) record.configuredCombinedEvModelSignals = signals;
        if (hasMinimum) record.combinedMinEdgeUsedMinimum = minimum;
        if (hasMaximum) record.combinedMinEdgeUsedMaximum = maximum;
    }
    if (version >= 7) {
        { int present = 0, value = 0;
          if (!(in >> present >> value)) return std::nullopt;
          if (present) record.activePaperPairHundredths = value; }
        { int present = 0, value = 0;
          if (!(in >> present >> value)) return std::nullopt;
          if (present) record.activePaperMainHundredths = value; }
        { int present = 0, value = 0;
          if (!(in >> present >> value)) return std::nullopt;
          if (present) record.activePaperSignals = value; }
        { int present = 0, value = 0;
          if (!(in >> present >> value)) return std::nullopt;
          if (present) record.confirmedActualHundredths = value; }
    }
    if (record.id.empty()) return std::nullopt;
    return record;
}

inline int RecordCompletenessScore(const Record& record) {
    int score = 0;
    score += !record.label.empty();
    score += !record.startIso.empty();
    score += !record.endIso.empty();
    score += !record.source.empty();
    score += record.legacyPeakToTroughDrawdown.has_value();
    score += record.highWaterUnits.has_value();
    score += record.activeDurationMs.has_value();
    score += record.bankrollLowUnits.has_value();
    score += record.startBalanceMinor.has_value();
    score += record.endBalanceMinor.has_value();
    score += !record.balanceCurrency.empty();
    score += record.unitsHundredths.has_value();
    score += record.minEdgeModelUnitsHundredths.has_value();
    score += record.positiveCombinedEvModelUnitsHundredths.has_value();
    score += record.minEdgeModelSignals.has_value();
    score += record.positiveCombinedEvModelSignals.has_value();
    score += record.combinedEvFilterEnabledAtSave.has_value();
    score += record.configuredCombinedEvModelUnitsHundredths.has_value();
    score += record.configuredCombinedEvModelSignals.has_value();
    score += record.combinedMinEdgeUsedMinimum.has_value();
    score += record.combinedMinEdgeUsedMaximum.has_value();
    score += record.activePaperPairHundredths.has_value();
    score += record.activePaperMainHundredths.has_value();
    score += record.activePaperSignals.has_value();
    score += record.confirmedActualHundredths.has_value();
    return score;
}

inline bool SameLogicalSession(const Record& a, const Record& b) {
    if (!a.id.empty() && a.id == b.id) return true;
    // The session start timestamp is stable for the lifetime of one UI session.
    // It therefore survives accidental creation of a second .session file with
    // another GUID and is the safest logical key for workbook de-duplication.
    if (!a.startIso.empty() && !b.startIso.empty())
        return a.startIso == b.startIso;
    // Very old historical rows had no timestamp.  Only collapse those when the
    // available metadata is identical, so two genuinely separate legacy
    // sessions are never merged merely because they have the same P/L.
    if (a.startIso.empty() && b.startIso.empty() &&
        !a.label.empty() && a.label == b.label &&
        a.unitsHundredths.value_or(a.units * 100) ==
            b.unitsHundredths.value_or(b.units * 100) &&
        a.activeDurationMs == b.activeDurationMs &&
        a.source == b.source)
        return true;
    return false;
}

inline bool PreferDuplicateCandidate(const Record& current,
                                     const Record& candidate) {
    const auto currentDuration = current.activeDurationMs.value_or(0);
    const auto candidateDuration = candidate.activeDurationMs.value_or(0);
    if (candidateDuration != currentDuration)
        return candidateDuration > currentDuration;
    if (candidate.endIso != current.endIso)
        return candidate.endIso > current.endIso;
    const int currentScore = RecordCompletenessScore(current);
    const int candidateScore = RecordCompletenessScore(candidate);
    if (candidateScore != currentScore)
        return candidateScore > currentScore;
    // Deterministic tie-breaker; the workbook never displays the internal id.
    return candidate.id < current.id;
}

inline void MergeDuplicateRecord(Record& current, const Record& candidate) {
    const std::string stableId = current.id;
    const bool preferCandidate = PreferDuplicateCandidate(current, candidate);
    const Record fallback = preferCandidate ? current : candidate;
    if (preferCandidate) current = candidate;
    // Keep the first internal id so repeated workbook rebuilds stay stable even
    // when directory iteration order changes.
    current.id = stableId;
    if (current.label.empty()) current.label = fallback.label;
    if (current.startIso.empty()) current.startIso = fallback.startIso;
    if (current.endIso.empty()) current.endIso = fallback.endIso;
    if (current.source.empty()) current.source = fallback.source;
    if (!current.legacyPeakToTroughDrawdown) current.legacyPeakToTroughDrawdown = fallback.legacyPeakToTroughDrawdown;
    if (!current.highWaterUnits) current.highWaterUnits = fallback.highWaterUnits;
    if (!current.activeDurationMs) current.activeDurationMs = fallback.activeDurationMs;
    if (!current.bankrollLowUnits) current.bankrollLowUnits = fallback.bankrollLowUnits;
    if (!current.startBalanceMinor) current.startBalanceMinor = fallback.startBalanceMinor;
    if (!current.endBalanceMinor) current.endBalanceMinor = fallback.endBalanceMinor;
    if (current.balanceCurrency.empty()) current.balanceCurrency = fallback.balanceCurrency;
    if (!current.unitsHundredths) current.unitsHundredths = fallback.unitsHundredths;
    if (!current.minEdgeModelUnitsHundredths) current.minEdgeModelUnitsHundredths = fallback.minEdgeModelUnitsHundredths;
    if (!current.positiveCombinedEvModelUnitsHundredths) current.positiveCombinedEvModelUnitsHundredths = fallback.positiveCombinedEvModelUnitsHundredths;
    if (!current.minEdgeModelSignals) current.minEdgeModelSignals = fallback.minEdgeModelSignals;
    if (!current.positiveCombinedEvModelSignals) current.positiveCombinedEvModelSignals = fallback.positiveCombinedEvModelSignals;
    if (!current.combinedEvFilterEnabledAtSave) current.combinedEvFilterEnabledAtSave = fallback.combinedEvFilterEnabledAtSave;
    // Never combine a partial/older configured model with a newer baseline.
    // All new fields form one snapshot; fill only from the same coverage.
    if (!current.configuredCombinedEvModelUnitsHundredths &&
        current.endIso == fallback.endIso && current.activeDurationMs == fallback.activeDurationMs &&
        current.minEdgeModelUnitsHundredths == fallback.minEdgeModelUnitsHundredths &&
        current.minEdgeModelSignals == fallback.minEdgeModelSignals) {
        current.configuredCombinedEvModelUnitsHundredths = fallback.configuredCombinedEvModelUnitsHundredths;
        current.configuredCombinedEvModelSignals = fallback.configuredCombinedEvModelSignals;
        current.combinedMinEdgeUsedMinimum = fallback.combinedMinEdgeUsedMinimum;
        current.combinedMinEdgeUsedMaximum = fallback.combinedMinEdgeUsedMaximum;
    }
    // The Paper and actual ledger are one snapshot, never fill from an older
    // session extent and thereby combine two different observation periods.
    if (!current.activePaperSignals && current.endIso == fallback.endIso &&
        current.activeDurationMs == fallback.activeDurationMs &&
        current.minEdgeModelSignals == fallback.minEdgeModelSignals) {
        current.activePaperPairHundredths = fallback.activePaperPairHundredths;
        current.activePaperMainHundredths = fallback.activePaperMainHundredths;
        current.activePaperSignals = fallback.activePaperSignals;
        current.confirmedActualHundredths = fallback.confirmedActualHundredths;
    }
}

inline void AppendOrMergeLogicalRecord(std::vector<Record>& records,
                                       const Record& record) {
    auto found = std::find_if(records.begin(), records.end(), [&](const Record& item) {
        return SameLogicalSession(item, record);
    });
    if (found == records.end()) records.push_back(record);
    else MergeDuplicateRecord(*found, record);
}

inline std::vector<Record> LoadAllRecords(const std::filesystem::path& directory) {
    std::vector<Record> records;
    for (const auto& historical : HistoricalRecords())
        AppendOrMergeLogicalRecord(records, historical);
    std::error_code ec;
    if (std::filesystem::exists(directory, ec)) {
        for (const auto& entry : std::filesystem::directory_iterator(directory, ec)) {
            if (ec) break;
            if (!entry.is_regular_file() || entry.path().extension() != L".session") continue;
            const auto parsed = ReadRecordFile(entry.path());
            if (!parsed) continue;
            AppendOrMergeLogicalRecord(records, *parsed);
        }
    }
    return records;
}

inline std::uint32_t Crc32(const std::string& data) {
    std::uint32_t crc = 0xffffffffU;
    for (unsigned char byte : data) {
        crc ^= byte;
        for (int bit = 0; bit < 8; ++bit)
            crc = (crc >> 1) ^ (0xedb88320U & (0U - (crc & 1U)));
    }
    return crc ^ 0xffffffffU;
}

inline void Put16(std::ofstream& out, std::uint16_t value) {
    const char bytes[2] = {static_cast<char>(value), static_cast<char>(value >> 8)};
    out.write(bytes, 2);
}

inline void Put32(std::ofstream& out, std::uint32_t value) {
    const char bytes[4] = {static_cast<char>(value), static_cast<char>(value >> 8),
        static_cast<char>(value >> 16), static_cast<char>(value >> 24)};
    out.write(bytes, 4);
}

inline bool ReplaceFileAtomically(const std::filesystem::path& source,
                                  const std::filesystem::path& target) {
#ifdef _WIN32
    return MoveFileExW(source.c_str(), target.c_str(),
                       MOVEFILE_REPLACE_EXISTING | MOVEFILE_WRITE_THROUGH) != FALSE;
#else
    std::error_code ec;
    std::filesystem::rename(source, target, ec);
    if (!ec) return true;
    // Portable test fallback: Windows production keeps the stricter MoveFileExW
    // behavior so an open Excel file remains detectable.
    std::filesystem::remove(target, ec);
    ec.clear();
    std::filesystem::rename(source, target, ec);
    return !ec;
#endif
}

struct ZipItem {
    std::string name;
    std::string data;
    std::uint32_t crc{0};
    std::uint32_t offset{0};
};

inline bool WriteStoreZip(const std::filesystem::path& path,
                          std::vector<ZipItem> items) {
    std::ofstream out(path, std::ios::binary | std::ios::trunc);
    if (!out) return false;
    for (auto& item : items) {
        item.crc = Crc32(item.data);
        item.offset = static_cast<std::uint32_t>(out.tellp());
        Put32(out, 0x04034b50U); Put16(out, 20); Put16(out, 0); Put16(out, 0);
        Put16(out, 0); Put16(out, 0x0021); Put32(out, item.crc);
        Put32(out, static_cast<std::uint32_t>(item.data.size()));
        Put32(out, static_cast<std::uint32_t>(item.data.size()));
        Put16(out, static_cast<std::uint16_t>(item.name.size())); Put16(out, 0);
        out.write(item.name.data(), static_cast<std::streamsize>(item.name.size()));
        out.write(item.data.data(), static_cast<std::streamsize>(item.data.size()));
    }
    const std::uint32_t centralOffset = static_cast<std::uint32_t>(out.tellp());
    for (const auto& item : items) {
        Put32(out, 0x02014b50U); Put16(out, 20); Put16(out, 20); Put16(out, 0);
        Put16(out, 0); Put16(out, 0); Put16(out, 0x0021); Put32(out, item.crc);
        Put32(out, static_cast<std::uint32_t>(item.data.size()));
        Put32(out, static_cast<std::uint32_t>(item.data.size()));
        Put16(out, static_cast<std::uint16_t>(item.name.size()));
        Put16(out, 0); Put16(out, 0); Put16(out, 0); Put16(out, 0); Put32(out, 0);
        Put32(out, item.offset);
        out.write(item.name.data(), static_cast<std::streamsize>(item.name.size()));
    }
    const std::uint32_t centralSize = static_cast<std::uint32_t>(out.tellp()) - centralOffset;
    Put32(out, 0x06054b50U); Put16(out, 0); Put16(out, 0);
    Put16(out, static_cast<std::uint16_t>(items.size()));
    Put16(out, static_cast<std::uint16_t>(items.size()));
    Put32(out, centralSize); Put32(out, centralOffset); Put16(out, 0);
    out.flush();
    return static_cast<bool>(out);
}

inline std::string InlineCell(const std::string& ref, const std::string& text, int style = 0) {
    std::ostringstream out;
    out << "<c r=\"" << ref << "\" t=\"inlineStr\"";
    if (style) out << " s=\"" << style << "\"";
    out << "><is><t xml:space=\"preserve\">" << XmlEscape(text) << "</t></is></c>";
    return out.str();
}

inline std::string NumberCell(const std::string& ref, double value, int style = 0) {
    std::ostringstream out;
    out << "<c r=\"" << ref << "\"";
    if (style) out << " s=\"" << style << "\"";
    out << "><v>" << std::setprecision(15) << value << "</v></c>";
    return out.str();
}

struct ThreeModelComparison {
    int sessions{0};
    long long minEdge{0}, positive{0}, configured{0};
    std::optional<double> minimum, maximum;
    bool thresholdsComplete{true};

    std::string ThresholdLabel() const {
        if (!sessions || !thresholdsComplete || !minimum || !maximum)
            return "siehe U/V je Session";
        const auto percent = [](double value) {
            std::ostringstream out;
            out << std::fixed << std::setprecision(2) << value * 100.0;
            std::string text = out.str();
            std::replace(text.begin(), text.end(), '.', ',');
            return text + " %";
        };
        return *minimum == *maximum ? percent(*minimum)
            : percent(*minimum) + " bis " + percent(*maximum);
    }

    std::string BestLabel() const {
        if (!sessions) return "Kein vollständiger Vergleich";
        const auto best = std::max({minEdge, positive, configured});
        if ((minEdge == best) + (positive == best) + (configured == best) > 1)
            return "Gleichstand an der Spitze";
        if (configured == best) return "Gesamt-MinEdge (" + ThresholdLabel() + ")";
        return positive == best ? "GesamtEV>0" : "MinEdge ohne Gesamtfilter";
    }
};

inline ThreeModelComparison CompareThreeModels(const std::vector<Record>& records) {
    ThreeModelComparison result;
    for (const auto& record : records) {
        // Only rank policies over identical recorded sessions. Missing legacy
        // models must never be interpreted as a zero result.
        if (!record.minEdgeModelUnitsHundredths ||
            !record.positiveCombinedEvModelUnitsHundredths ||
            !record.configuredCombinedEvModelUnitsHundredths) continue;
        ++result.sessions;
        result.minEdge += *record.minEdgeModelUnitsHundredths;
        result.positive += *record.positiveCombinedEvModelUnitsHundredths;
        result.configured += *record.configuredCombinedEvModelUnitsHundredths;
        if (!record.combinedMinEdgeUsedMinimum || !record.combinedMinEdgeUsedMaximum) {
            result.thresholdsComplete = false;
            continue;
        }
        const auto low = *record.combinedMinEdgeUsedMinimum;
        const auto high = *record.combinedMinEdgeUsedMaximum;
        result.minimum = result.minimum ? std::min(*result.minimum, low) : low;
        result.maximum = result.maximum ? std::max(*result.maximum, high) : high;
    }
    return result;
}

inline bool WriteWorkbook(const std::filesystem::path& workbook,
                          const std::vector<Record>& records,
                          std::wstring& error) {
    const std::string contentTypes =
        "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
        "<Types xmlns=\"http://schemas.openxmlformats.org/package/2006/content-types\">"
        "<Default Extension=\"rels\" ContentType=\"application/vnd.openxmlformats-package.relationships+xml\"/>"
        "<Default Extension=\"xml\" ContentType=\"application/xml\"/>"
        "<Override PartName=\"/xl/workbook.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml\"/>"
        "<Override PartName=\"/xl/worksheets/sheet1.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml\"/>"
        "<Override PartName=\"/xl/styles.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml\"/>"
        "</Types>";
    const std::string rootRels =
        "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
        "<Relationships xmlns=\"http://schemas.openxmlformats.org/package/2006/relationships\">"
        "<Relationship Id=\"rId1\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument\" Target=\"xl/workbook.xml\"/>"
        "</Relationships>";
    const std::string workbookXml =
        "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
        "<workbook xmlns=\"http://schemas.openxmlformats.org/spreadsheetml/2006/main\" xmlns:r=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships\">"
        "<sheets><sheet name=\"Sessions\" sheetId=\"1\" r:id=\"rId1\"/></sheets>"
        "<calcPr calcMode=\"auto\" fullCalcOnLoad=\"1\" forceFullCalc=\"1\"/></workbook>";
    const std::string workbookRels =
        "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
        "<Relationships xmlns=\"http://schemas.openxmlformats.org/package/2006/relationships\">"
        "<Relationship Id=\"rId1\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet\" Target=\"worksheets/sheet1.xml\"/>"
        "<Relationship Id=\"rId2\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles\" Target=\"styles.xml\"/>"
        "</Relationships>";
    const std::string styles =
        "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
        "<styleSheet xmlns=\"http://schemas.openxmlformats.org/spreadsheetml/2006/main\">"
        "<numFmts count=\"1\"><numFmt numFmtId=\"164\" formatCode=\"[h]:mm:ss\"/></numFmts>"
        "<fonts count=\"3\"><font><sz val=\"11\"/><name val=\"Aptos\"/></font>"
        "<font><b/><sz val=\"16\"/><color rgb=\"FFFFFFFF\"/><name val=\"Aptos Display\"/></font>"
        "<font><b/><sz val=\"11\"/><color rgb=\"FFFFFFFF\"/><name val=\"Aptos\"/></font></fonts>"
        "<fills count=\"4\"><fill><patternFill patternType=\"none\"/></fill><fill><patternFill patternType=\"gray125\"/></fill>"
        "<fill><patternFill patternType=\"solid\"><fgColor rgb=\"FF17365D\"/><bgColor indexed=\"64\"/></patternFill></fill>"
        "<fill><patternFill patternType=\"solid\"><fgColor rgb=\"FF2F75B5\"/><bgColor indexed=\"64\"/></patternFill></fill></fills>"
        "<borders count=\"1\"><border><left/><right/><top/><bottom/><diagonal/></border></borders>"
        "<cellStyleXfs count=\"1\"><xf numFmtId=\"0\" fontId=\"0\" fillId=\"0\" borderId=\"0\"/></cellStyleXfs>"
        "<cellXfs count=\"7\"><xf numFmtId=\"0\" fontId=\"0\" fillId=\"0\" borderId=\"0\" xfId=\"0\"/>"
        "<xf numFmtId=\"0\" fontId=\"1\" fillId=\"2\" borderId=\"0\" xfId=\"0\" applyFont=\"1\" applyFill=\"1\"/>"
        "<xf numFmtId=\"0\" fontId=\"2\" fillId=\"3\" borderId=\"0\" xfId=\"0\" applyFont=\"1\" applyFill=\"1\" applyAlignment=\"1\"><alignment wrapText=\"1\" vertical=\"center\"/></xf>"
        "<xf numFmtId=\"164\" fontId=\"0\" fillId=\"0\" borderId=\"0\" xfId=\"0\" applyNumberFormat=\"1\"/>"
        "<xf numFmtId=\"0\" fontId=\"0\" fillId=\"0\" borderId=\"0\" xfId=\"0\" applyAlignment=\"1\"><alignment wrapText=\"1\" vertical=\"top\"/></xf>"
        "<xf numFmtId=\"4\" fontId=\"0\" fillId=\"0\" borderId=\"0\" xfId=\"0\" applyNumberFormat=\"1\"/>"
        "<xf numFmtId=\"10\" fontId=\"0\" fillId=\"0\" borderId=\"0\" xfId=\"0\" applyNumberFormat=\"1\"/>"
        "</cellXfs><cellStyles count=\"1\"><cellStyle name=\"Normal\" xfId=\"0\" builtinId=\"0\"/></cellStyles></styleSheet>";

    long long totalUnitsHundredths = 0;
    for (const auto& record : records)
        totalUnitsHundredths += record.unitsHundredths.value_or(record.units * 100);
    const double totalUnits = static_cast<double>(totalUnitsHundredths) / 100.0;
    const int lastRow = static_cast<int>(records.size()) + 4;
    std::ostringstream sheet;
    sheet << "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
          << "<worksheet xmlns=\"http://schemas.openxmlformats.org/spreadsheetml/2006/main\">"
          << "<dimension ref=\"A1:AA" << lastRow << "\"/>"
          << "<sheetViews><sheetView workbookViewId=\"0\"><pane ySplit=\"4\" topLeftCell=\"A5\" activePane=\"bottomLeft\" state=\"frozen\"/></sheetView></sheetViews>"
          << "<sheetFormatPr defaultRowHeight=\"15\"/>"
          << "<cols><col min=\"1\" max=\"1\" width=\"31\" customWidth=\"1\"/><col min=\"2\" max=\"3\" width=\"23\" customWidth=\"1\"/>"
          << "<col min=\"4\" max=\"4\" width=\"16\" customWidth=\"1\"/><col min=\"5\" max=\"7\" width=\"19\" customWidth=\"1\"/>"
          << "<col min=\"8\" max=\"10\" width=\"18\" customWidth=\"1\"/>"
          << "<col min=\"11\" max=\"13\" width=\"22\" customWidth=\"1\"/>"
          << "<col min=\"14\" max=\"15\" width=\"18\" customWidth=\"1\"/>"
          << "<col min=\"16\" max=\"16\" width=\"22\" customWidth=\"1\"/>"
          << "<col min=\"17\" max=\"17\" width=\"46\" customWidth=\"1\"/>"
          << "<col min=\"18\" max=\"27\" width=\"24\" customWidth=\"1\"/></cols><sheetData>";
    sheet << "<row r=\"1\" ht=\"28\" customHeight=\"1\">" << InlineCell("A1", "Baccarat Counter – zentraler Sessionverlauf", 1) << "</row>";
    long long totalMinEdgeModelHundredths = 0;
    long long totalPositiveModelHundredths = 0;
    long long totalConfiguredModelHundredths = 0, totalConfiguredDeltaHundredths = 0;
    int configuredSessions = 0, configuredDeltaSessions = 0;
    for (const auto& record : records) {
        totalMinEdgeModelHundredths += record.minEdgeModelUnitsHundredths.value_or(0);
        totalPositiveModelHundredths += record.positiveCombinedEvModelUnitsHundredths.value_or(0);
        if (record.configuredCombinedEvModelUnitsHundredths) {
            ++configuredSessions;
            totalConfiguredModelHundredths += *record.configuredCombinedEvModelUnitsHundredths;
            if (record.minEdgeModelUnitsHundredths) {
                ++configuredDeltaSessions;
                totalConfiguredDeltaHundredths += *record.configuredCombinedEvModelUnitsHundredths -
                    *record.minEdgeModelUnitsHundredths;
            }
        }
    }
    const double totalMinEdgeModel = static_cast<double>(totalMinEdgeModelHundredths) / 100.0;
    const double totalPositiveModel = static_cast<double>(totalPositiveModelHundredths) / 100.0;
    const auto comparison = CompareThreeModels(records);
    sheet << "<row r=\"2\" ht=\"48\" customHeight=\"1\">" << InlineCell("A2", "Abrechnung (Stopps/Kurve):", 2)
          << "<c r=\"B2\" s=\"5\"><f>SUM(E5:E" << (records.size() + 4)
          << ")</f><v>" << std::setprecision(15) << totalUnits << "</v></c>"
          << InlineCell("C2", "Modell MinEdge:", 2)
          << "<c r=\"D2\" s=\"5\"><f>SUM(K5:K" << (records.size() + 4)
          << ")</f><v>" << std::setprecision(15) << totalMinEdgeModel << "</v></c>"
          << InlineCell("E2", "Modell GesamtEV>0:", 2)
          << "<c r=\"F2\" s=\"5\"><f>SUM(L5:L" << (records.size() + 4)
          << ")</f><v>" << std::setprecision(15) << totalPositiveModel << "</v></c>"
          << InlineCell("G2", "Delta GesamtEV - MinEdge:", 2)
          << "<c r=\"H2\" s=\"5\"><f>F2-D2</f><v>"
          << std::setprecision(15) << (totalPositiveModel - totalMinEdgeModel)
          << "</v></c>"
          << InlineCell("I2", "Bestes der drei Modelle (gleiche Sessions):", 2)
          << "<c r=\"J2\" t=\"str\" s=\"4\"><f>"
          << XmlEscape("IF(COUNT(T2,V2,X2)<3,\"Kein vollständiger Vergleich\","
                       "IF(COUNTIF(T2,MAX(T2,V2,X2))+COUNTIF(V2,MAX(T2,V2,X2))+COUNTIF(X2,MAX(T2,V2,X2))>1,"
                       "\"Gleichstand an der Spitze\",IF(X2=MAX(T2,V2,X2),\"Gesamt-MinEdge (\"&Z2&\")\","
                       "IF(V2=MAX(T2,V2,X2),\"GesamtEV>0\",\"MinEdge ohne Gesamtfilter\"))))")
          << "</f><v>" << XmlEscape(comparison.BestLabel()) << "</v></c>"
          << InlineCell("K2", "Modell Gesamt-MinEdge:", 2);
    if (configuredSessions > 0)
        sheet << "<c r=\"L2\" s=\"5\"><f>SUM(R5:R" << lastRow << ")</f><v>"
              << static_cast<double>(totalConfiguredModelHundredths) / 100.0 << "</v></c>";
    sheet << InlineCell("M2", "Delta zur MinEdge-Basis (gleiche Sessions):", 2);
    if (configuredDeltaSessions > 0)
        sheet << "<c r=\"N2\" s=\"5\"><f>SUM(S5:S" << lastRow << ")</f><v>"
              << static_cast<double>(totalConfiguredDeltaHundredths) / 100.0 << "</v></c>";
    const auto matchedFormula = [&](const char* ref, char column, long long total) {
        if (!comparison.sessions) return;
        const std::string end = std::to_string(lastRow);
        const std::string formula = "SUMPRODUCT(ISNUMBER(K5:K" + end +
            ")*ISNUMBER(L5:L" + end + ")*ISNUMBER(R5:R" + end +
            ")," + column + "5:" + column + end + ")";
        sheet << "<c r=\"" << ref << "\" s=\"5\"><f>" << XmlEscape(formula)
              << "</f><v>" << static_cast<double>(total) / 100.0 << "</v></c>";
    };
    sheet << InlineCell("O2", "Sessions mit neuem Modell:", 2)
          << NumberCell("P2", configuredSessions)
          << InlineCell("Q2", "Dreiervergleich: gemeinsame Sessions", 2)
          << NumberCell("R2", comparison.sessions)
          << InlineCell("S2", "Vergleich: MinEdge ohne Gesamtfilter", 2);
    matchedFormula("T2", 'K', comparison.minEdge);
    sheet << InlineCell("U2", "Vergleich: MinEdge + GesamtEV>0", 2);
    matchedFormula("V2", 'L', comparison.positive);
    sheet << InlineCell("W2", "Vergleich: MinEdge + Gesamt-MinEdge", 2);
    matchedFormula("X2", 'R', comparison.configured);
    sheet << InlineCell("Y2", "Gesamt-MinEdge im Dreiervergleich", 2)
          << InlineCell("Z2", comparison.ThresholdLabel(), 4);
    sheet << "</row>";
    sheet << "<row r=\"3\" ht=\"60\" customHeight=\"1\">"
          << InlineCell("A3", "Alle Gesamtmodelle enthalten die Pflicht-Hauptwette. MinEdge: ohne Gesamtfilter; GesamtEV>0: zusätzlich strikt positiv. J2 vergleicht drei Modelle nur über gemeinsame Sessions (R2, T2/V2/X2). Historische Lücken bleiben leer.", 4)
          << InlineCell("Q3", "Ab v21.2.110: Gesamt-MinEdge-Modell unabhängig vom Live-Filter; Grenze je Signal. U/V: kleinster/größter verwendeter Wert, leer ohne abgerechnete Signale.", 4)
          << InlineCell("W3", "Ab v21.2.113: Paper aktiv folgt dem beim Signal gültigen Filter, inkl. Pflicht-Hauptwette. Ist enthält ausschließlich bestätigte Chips. Abrechnung/Stopps/Kurve behält das bisherige Modell; im Paper-Modus kein Echtgeld.", 4)
          << "</row>";
    sheet << "<row r=\"4\" ht=\"48\" customHeight=\"1\">";
    const char* headers[] = {
        "Session", "Start", "Ende", "Aktive Dauer", "Abrechnung Units",
        "Max. Minus (Startbankroll)", "Höchststand", "Startbalance", "Endbalance", "Währung",
        "Modell MinEdge Units", "Modell GesamtEV>0 Units", "Delta GesamtEV - MinEdge",
        "MinEdge-Modell Signale", "GesamtEV>0 Signale", "GesamtEV-Filter beim Speichern", "Hinweise",
        "Modell Gesamt-MinEdge Units", "Delta Gesamt-MinEdge - MinEdge",
        "Gesamt-MinEdge Signale", "Gesamt-MinEdge verwendet (Min)", "Gesamt-MinEdge verwendet (Max)",
        "Paper aktiv: Pair Units", "Paper aktiv: Hauptwette Units", "Paper aktiv: Signale",
        "Ist Units (nur bestätigt)", "Paper aktiv: Gesamt Units"};
    for (int i = 0; i < 27; ++i) {
        std::string ref;
        if (i < 26) ref = std::string(1, static_cast<char>('A' + i)) + "4";
        else ref = "AA4";
        sheet << InlineCell(ref, headers[i], 2);
    }
    sheet << "</row>";
    for (std::size_t i = 0; i < records.size(); ++i) {
        const auto& record = records[i];
        const int row = static_cast<int>(i) + 5;
        const auto ref = [row](char column) { return std::string(1, column) + std::to_string(row); };
        sheet << "<row r=\"" << row << "\">" << InlineCell(ref('A'), record.label);
        if (!record.startIso.empty()) sheet << InlineCell(ref('B'), record.startIso);
        if (!record.endIso.empty()) sheet << InlineCell(ref('C'), record.endIso);
        if (record.activeDurationMs) sheet << NumberCell(ref('D'), static_cast<double>(*record.activeDurationMs) / 86400000.0, 3);
        const double exactUnits = static_cast<double>(
            record.unitsHundredths.value_or(record.units * 100)) / 100.0;
        sheet << NumberCell(ref('E'), exactUnits, 5);
        if (record.bankrollLowUnits) sheet << NumberCell(ref('F'), *record.bankrollLowUnits);
        if (record.highWaterUnits) sheet << NumberCell(ref('G'), *record.highWaterUnits);
        if (record.startBalanceMinor)
            sheet << NumberCell(ref('H'), static_cast<double>(*record.startBalanceMinor) / 100.0, 5);
        if (record.endBalanceMinor)
            sheet << NumberCell(ref('I'), static_cast<double>(*record.endBalanceMinor) / 100.0, 5);
        if (!record.balanceCurrency.empty())
            sheet << InlineCell(ref('J'), record.balanceCurrency);
        if (record.minEdgeModelUnitsHundredths)
            sheet << NumberCell(ref('K'), static_cast<double>(*record.minEdgeModelUnitsHundredths) / 100.0, 5);
        if (record.positiveCombinedEvModelUnitsHundredths)
            sheet << NumberCell(ref('L'), static_cast<double>(*record.positiveCombinedEvModelUnitsHundredths) / 100.0, 5);
        if (record.minEdgeModelUnitsHundredths && record.positiveCombinedEvModelUnitsHundredths)
            sheet << NumberCell(ref('M'), static_cast<double>(
                *record.positiveCombinedEvModelUnitsHundredths -
                *record.minEdgeModelUnitsHundredths) / 100.0, 5);
        if (record.minEdgeModelSignals) sheet << NumberCell(ref('N'), *record.minEdgeModelSignals);
        if (record.positiveCombinedEvModelSignals) sheet << NumberCell(ref('O'), *record.positiveCombinedEvModelSignals);
        if (record.combinedEvFilterEnabledAtSave)
            sheet << InlineCell(ref('P'), *record.combinedEvFilterEnabledAtSave ? "EIN" : "AUS");
        std::string notes = record.source;
        if (!record.bankrollLowUnits && record.legacyPeakToTroughDrawdown)
            notes += (notes.empty() ? "" : "; ") + std::string("früherer Peak-to-Trough-Drawdown: ") + std::to_string(*record.legacyPeakToTroughDrawdown) + " u";
        sheet << InlineCell(ref('Q'), notes, 4);
        if (record.configuredCombinedEvModelUnitsHundredths) {
            sheet << NumberCell(ref('R'), static_cast<double>(*record.configuredCombinedEvModelUnitsHundredths) / 100.0, 5);
            if (record.minEdgeModelUnitsHundredths)
                sheet << "<c r=\"" << ref('S') << "\" s=\"5\"><f>" << ref('R') << "-" << ref('K')
                      << "</f><v>" << static_cast<double>(*record.configuredCombinedEvModelUnitsHundredths -
                          *record.minEdgeModelUnitsHundredths) / 100.0 << "</v></c>";
        }
        if (record.configuredCombinedEvModelSignals)
            sheet << NumberCell(ref('T'), *record.configuredCombinedEvModelSignals);
        if (record.combinedMinEdgeUsedMinimum)
            sheet << NumberCell(ref('U'), *record.combinedMinEdgeUsedMinimum, 6);
        if (record.combinedMinEdgeUsedMaximum)
            sheet << NumberCell(ref('V'), *record.combinedMinEdgeUsedMaximum, 6);
        if (record.activePaperPairHundredths)
            sheet << NumberCell(ref('W'), *record.activePaperPairHundredths / 100.0, 5);
        if (record.activePaperMainHundredths)
            sheet << NumberCell(ref('X'), *record.activePaperMainHundredths / 100.0, 5);
        if (record.activePaperSignals)
            sheet << NumberCell(ref('Y'), *record.activePaperSignals);
        if (record.confirmedActualHundredths)
            sheet << NumberCell(ref('Z'), *record.confirmedActualHundredths / 100.0, 5);
        if (record.activePaperPairHundredths && record.activePaperMainHundredths)
            sheet << "<c r=\"AA" << row << "\" s=\"5\"><f>" << ref('W') << "+" << ref('X')
                  << "</f><v>" << (*record.activePaperPairHundredths + *record.activePaperMainHundredths) / 100.0
                  << "</v></c>";
        sheet << "</row>";
    }
    sheet << "</sheetData><autoFilter ref=\"A4:AA" << lastRow << "\"/>"
          << "<pageMargins left=\"0.5\" right=\"0.5\" top=\"0.6\" bottom=\"0.6\" header=\"0.3\" footer=\"0.3\"/>"
          << "</worksheet>";

    std::error_code ec;
    std::filesystem::create_directories(workbook.parent_path(), ec);
    if (ec) { error = L"Zentraler BaccaratCounter-Ordner konnte nicht angelegt werden."; return false; }
    const auto tempPath = workbook.parent_path() / L"Sessionverlauf.tmp.xlsx";
    std::vector<ZipItem> items{
        {"[Content_Types].xml", contentTypes}, {"_rels/.rels", rootRels},
        {"xl/workbook.xml", workbookXml}, {"xl/_rels/workbook.xml.rels", workbookRels},
        {"xl/styles.xml", styles}, {"xl/worksheets/sheet1.xml", sheet.str()}
    };
    if (!WriteStoreZip(tempPath, std::move(items))) {
        error = L"Excel-Datei konnte nicht erstellt werden.";
        return false;
    }
    if (!ReplaceFileAtomically(tempPath, workbook)) {
        std::filesystem::remove(tempPath, ec);
        error = L"Session ist vorgemerkt; Sessionverlauf.xlsx ist vermutlich noch in Excel geöffnet.";
        return false;
    }
    return true;
}

inline bool SaveAndExport(const std::filesystem::path& baseDirectory,
                          const Record& record,
                          std::wstring& error) {
    const auto sessions = baseDirectory / L"Sessions";
    if (!WriteRecordFile(sessions, record, error)) return false;
    return WriteWorkbook(baseDirectory / L"Sessionverlauf.xlsx", LoadAllRecords(sessions), error);
}

inline bool EnsureWorkbook(const std::filesystem::path& baseDirectory,
                           std::wstring& error) {
    return WriteWorkbook(baseDirectory / L"Sessionverlauf.xlsx",
                         LoadAllRecords(baseDirectory / L"Sessions"), error);
}

} // namespace session_export
