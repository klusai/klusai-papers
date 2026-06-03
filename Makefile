.PHONY: help results europriv-bench synthetic-drift underserved-sota privacy-utility dissociation-protector clean

# Source of truth for benchmark numbers. Override for a sibling checkout layout if needed.
LEADERBOARD := ../europriv-bench/baselines/leaderboard.json

help:
	@echo "  make results        - pull the committed leaderboard into results/ (reproducible builds)"
	@echo "Build a paper PDF (requires latexmk + TeX):"
	@echo "  make europriv-bench"
	@echo "  make synthetic-drift"
	@echo "  make underserved-sota"
	@echo "  make privacy-utility"
	@echo "  make dissociation-protector  (KLU-110 skeleton draft)"

results:
	@mkdir -p results
	@if [ -f "$(LEADERBOARD)" ]; then \
		cp "$(LEADERBOARD)" results/leaderboard.json; \
		echo "copied $(LEADERBOARD) -> results/leaderboard.json"; \
	else \
		echo "leaderboard not found at $(LEADERBOARD); run 'europriv run' in europriv-bench first"; \
		exit 1; \
	fi
	@echo "TODO: validate results/leaderboard.json against europriv_bench's versioned results schema before \\input"

define build_paper
	cd papers/$(1) && latexmk -pdf main.tex
endef

europriv-bench:
	$(call build_paper,europriv-bench)

synthetic-drift:
	$(call build_paper,synthetic-drift)

underserved-sota:
	$(call build_paper,underserved-sota)

privacy-utility:
	$(call build_paper,privacy-utility)

dissociation-protector:
	$(call build_paper,dissociation-protector)

clean:
	find papers -name '*.aux' -o -name '*.log' -o -name '*.out' -o -name '*.fls' -o -name '*.fdb_latexmk' | xargs rm -f
