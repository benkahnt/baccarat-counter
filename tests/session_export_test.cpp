#include "session_export.h"
#include <cassert>
#include <iostream>
int main() {
    namespace fs = std::filesystem;
    const fs::path base = ".validation/out/BaccaratCounter";
    assert(fs::absolute(base).lexically_normal() ==
           fs::current_path() / ".validation" / "out" / "BaccaratCounter");
    fs::remove_all(base);
    assert(session_export::LoadAllRecords(base / "Sessions").empty());
    std::wstring emptyError;
    assert(session_export::EnsureWorkbook(base, emptyError));
    assert(fs::exists(base / "Sessionverlauf.xlsx"));
    session_export::Record current{
        "test-session", "Session Test", "2026-09-13T10:00:00.000",
        "2026-09-17T14:12:34.000", -18, std::nullopt, 8,
        "v54 test", 360754000ULL, -30, 500000, 498400, "EUR"};
    std::wstring error;
    assert(session_export::SaveAndExport(base, current, error));
    current.units = -16;
    current.unitsHundredths = -1575;
    current.minEdgeModelUnitsHundredths = 825;
    current.positiveCombinedEvModelUnitsHundredths = 1175;
    current.minEdgeModelSignals = 14;
    current.positiveCombinedEvModelSignals = 9;
    current.combinedEvFilterEnabledAtSave = true;
    current.configuredCombinedEvModelUnitsHundredths = 1475;
    current.configuredCombinedEvModelSignals = 7;
    current.combinedMinEdgeUsedMinimum = .0025;
    current.combinedMinEdgeUsedMaximum = .0025;
    current.activePaperPairHundredths = -2600;
    current.activePaperMainHundredths = 2900;
    current.activePaperSignals = 13;
    current.confirmedActualHundredths = 0;
    assert(session_export::SaveAndExport(base, current, error));
    {
        std::ofstream old(base / "Sessions" / "legacy.session", std::ios::binary);
        old << "BaccaratCounterSession 1\n"
            << std::quoted(std::string("legacy-v51")) << '\n'
            << std::quoted(std::string("v51 kompatibel")) << '\n'
            << std::quoted(std::string("2026-09-01T10:00:00.000")) << '\n'
            << std::quoted(std::string("2026-09-01T12:00:00.000")) << '\n'
            << 10 << '\n' << 1 << ' ' << 40 << '\n' << 1 << ' ' << 12 << '\n'
            << std::quoted(std::string("alte Session")) << '\n';
    }
    {
        std::ofstream v2(base / "Sessions" / "legacy-v52.session", std::ios::binary);
        v2 << "BaccaratCounterSession 2\n"
           << std::quoted(std::string("legacy-v52")) << '\n'
           << std::quoted(std::string("v52 kompatibel")) << '\n'
           << std::quoted(std::string("2026-09-02T10:00:00.000")) << '\n'
           << std::quoted(std::string("2026-09-02T11:00:00.000")) << '\n'
           << 0 << '\n' << 0 << ' ' << 0 << '\n' << 1 << ' ' << 4 << '\n'
           << std::quoted(std::string("v2 Session")) << '\n'
           << 1 << ' ' << 3600000ULL << '\n' << 1 << ' ' << -6 << '\n';
    }
    // v21.2.103: simulate an accidental second file for the same logical
    // UI session. The GUID differs, but startIso is identical. The workbook
    // must keep one row and use the later/more complete snapshot.
    {
        session_export::Record duplicate = current;
        duplicate.id = "duplicate-guid-for-same-session";
        duplicate.endIso = "2026-09-17T14:30:00.000";
        duplicate.activeDurationMs = 361000000ULL;
        duplicate.source = "newer duplicate snapshot";
        assert(session_export::WriteRecordFile(base / "Sessions", duplicate, error));
    }
    assert(session_export::EnsureWorkbook(base, error));
    auto all = session_export::LoadAllRecords(base / "Sessions");
    assert(all.size() == 3);
    int sum = 0; for (const auto& row : all) sum += row.units;
    assert(sum == -6);
    auto legacy = std::find_if(all.begin(), all.end(), [](const auto& r){return r.id=="legacy-v51";});
    assert(legacy != all.end());
    assert(!legacy->bankrollLowUnits.has_value());
    assert(legacy->legacyPeakToTroughDrawdown.value() == 40);
    auto legacyV52 = std::find_if(all.begin(), all.end(), [](const auto& r){return r.id=="legacy-v52";});
    assert(legacyV52 != all.end());
    assert(!legacyV52->startBalanceMinor.has_value());
    assert(!legacyV52->endBalanceMinor.has_value());
    auto saved = std::find_if(all.begin(), all.end(), [](const auto& r){
        return r.startIso=="2026-09-13T10:00:00.000";
    });
    assert(saved != all.end());
    assert(saved->startBalanceMinor.value() == 500000);
    assert(saved->endBalanceMinor.value() == 498400);
    assert(saved->balanceCurrency == "EUR");
    assert(saved->unitsHundredths.has_value());
    assert(*saved->unitsHundredths == -1575);
    assert(saved->minEdgeModelUnitsHundredths.value() == 825);
    assert(saved->positiveCombinedEvModelUnitsHundredths.value() == 1175);
    assert(saved->minEdgeModelSignals.value() == 14);
    assert(saved->positiveCombinedEvModelSignals.value() == 9);
    assert(saved->combinedEvFilterEnabledAtSave.value());
    assert(saved->configuredCombinedEvModelUnitsHundredths.value() == 1475);
    assert(saved->configuredCombinedEvModelSignals.value() == 7);
    assert(saved->combinedMinEdgeUsedMinimum.value() == .0025);
    assert(saved->combinedMinEdgeUsedMaximum.value() == .0025);
    assert(saved->activePaperPairHundredths.value() == -2600);
    assert(saved->activePaperMainHundredths.value() == 2900);
    assert(saved->activePaperSignals.value() == 13);
    assert(saved->confirmedActualHundredths.value() == 0);
    assert(!legacy->configuredCombinedEvModelUnitsHundredths);
    assert(saved->endIso == "2026-09-17T14:30:00.000");
    assert(saved->activeDurationMs.value() == 361000000ULL);
    assert(saved->source == "newer duplicate snapshot");
    assert(std::count_if(all.begin(), all.end(), [](const auto& r){
        return r.startIso=="2026-09-13T10:00:00.000";
    }) == 1);
    // A pre-v110 v5 file must remain readable without invented new results.
    {
        std::ifstream input(base / "Sessions" / "test-session.session");
        std::vector<std::string> lines;
        for (std::string line; std::getline(input, line);) lines.push_back(line);
        assert(lines.size() == 28);  // v7 appends four optional ledger fields.
        std::ofstream out(base / "legacy-v5.fixture");
        out << "BaccaratCounterSession 5\n";
        for (std::size_t i = 1; i < 20; ++i) out << lines[i] << '\n';
        out.close();
        auto old = session_export::ReadRecordFile(base / "legacy-v5.fixture");
        assert(old && old->positiveCombinedEvModelUnitsHundredths.value() == 1175);
        assert(!old->configuredCombinedEvModelUnitsHundredths && !old->combinedMinEdgeUsedMinimum);
        assert(!old->activePaperSignals && !old->confirmedActualHundredths);
        // v6 retains its configured-policy fields, but has no Paper/Ist ledger.
        {
            std::ofstream v6(base / "legacy-v6.fixture");
            v6 << "BaccaratCounterSession 6\n";
            for (std::size_t i = 1; i < 24; ++i) v6 << lines[i] << '\n';
        }
        const auto previous = session_export::ReadRecordFile(base / "legacy-v6.fixture");
        assert(previous && previous->configuredCombinedEvModelSignals.value() == 7);
        assert(!previous->activePaperSignals && !previous->confirmedActualHundredths);
        // A newer snapshot without the new model must not acquire stale values.
        old->endIso = "2026-09-18T14:30:00.000";
        old->activeDurationMs = 400000000ULL;
        session_export::MergeDuplicateRecord(*old, current);
        assert(!old->configuredCombinedEvModelUnitsHundredths);
        assert(!old->activePaperSignals && !old->confirmedActualHundredths);
    }
    // Preserve known zeros and differing thresholds, including filter OFF.
    auto zero = current;
    zero.id = "zero-fixture";
    zero.configuredCombinedEvModelUnitsHundredths = 0;
    zero.configuredCombinedEvModelSignals = 0;
    zero.combinedMinEdgeUsedMinimum = 0;
    zero.combinedMinEdgeUsedMaximum = .0225;
    zero.combinedEvFilterEnabledAtSave = false;
    assert(session_export::WriteRecordFile(base / "fixtures", zero, error));
    auto loadedZero = session_export::ReadRecordFile(base / "fixtures/zero-fixture.session");
    assert(loadedZero && loadedZero->configuredCombinedEvModelUnitsHundredths.value() == 0);
    assert(loadedZero->configuredCombinedEvModelSignals.value() == 0);
    assert(loadedZero->combinedMinEdgeUsedMinimum.value() == 0);
    assert(loadedZero->combinedMinEdgeUsedMaximum.value() == .0225);
    assert(!loadedZero->combinedEvFilterEnabledAtSave.value());
    // The new summary must ignore old-only baselines, not subtract all history.
    auto oldOnly = current;
    oldOnly.id = "old-only"; oldOnly.label = "Old only";
    oldOnly.configuredCombinedEvModelUnitsHundredths.reset();
    oldOnly.configuredCombinedEvModelSignals.reset();
    oldOnly.combinedMinEdgeUsedMinimum.reset();
    oldOnly.combinedMinEdgeUsedMaximum.reset();
    oldOnly.minEdgeModelUnitsHundredths = -50000;
    zero.minEdgeModelUnitsHundredths = 0;
    assert(session_export::WriteWorkbook(base / "coverage.xlsx", {current, oldOnly, zero}, error));
    assert(session_export::WriteWorkbook(base / "legacy-only.xlsx", {oldOnly}, error));
    // Reproduce the overnight audit: the previously omitted third policy wins.
    auto overnight = current;
    overnight.minEdgeModelUnitsHundredths = -7075;
    overnight.positiveCombinedEvModelUnitsHundredths = -7175;
    overnight.configuredCombinedEvModelUnitsHundredths = -5575;
    auto previous = overnight;
    previous.minEdgeModelUnitsHundredths = -600;
    previous.positiveCombinedEvModelUnitsHundredths = -600;
    previous.configuredCombinedEvModelUnitsHundredths = -1100;
    const auto comparison = session_export::CompareThreeModels({overnight, previous, oldOnly});
    assert(comparison.sessions == 2);
    assert(comparison.minEdge == -7675 && comparison.positive == -7775 && comparison.configured == -6675);
    assert(comparison.ThresholdLabel() == "0,25 %");
    assert(comparison.BestLabel() == "Gesamt-MinEdge (0,25 %)");
    assert(session_export::CompareThreeModels({oldOnly}).BestLabel() == "Kein vollständiger Vergleich");
    auto tied = overnight;
    tied.configuredCombinedEvModelUnitsHundredths = -7075;
    assert(session_export::CompareThreeModels({tied}).BestLabel() == "Gleichstand an der Spitze");
    tied.minEdgeModelUnitsHundredths = 0;
    assert(session_export::CompareThreeModels({tied}).BestLabel() == "MinEdge ohne Gesamtfilter");
    tied.positiveCombinedEvModelUnitsHundredths = 1;
    assert(session_export::CompareThreeModels({tied}).BestLabel() == "GesamtEV>0");
    auto unknownThreshold = overnight;
    unknownThreshold.combinedMinEdgeUsedMinimum.reset();
    assert(session_export::CompareThreeModels({unknownThreshold}).ThresholdLabel() == "siehe U/V je Session");
    assert(session_export::CompareThreeModels({current, zero}).ThresholdLabel() == "0,00 % bis 2,25 %");
    assert(session_export::WriteWorkbook(base / "three-models.xlsx", {overnight, previous, oldOnly}, error));
    std::cout << "session export OK\n";
}
