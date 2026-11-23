# Explore the Sentinel-2 NDCI table in R.
# No Python or Earth Engine needed: reads the CSV the GitHub Action publishes.

library(ggplot2)

# Either the online copy (always current) or a local clone of the repo
src <- Sys.getenv("NDCI_CSV", "data/reservoir_ndci.csv")
# src <- "https://kristofm854.github.io/embalses-s2-monitor/data/reservoir_ndci.csv"
ts <- read.csv(src, comment.char = "#")  # lines starting with # describe the columns
ts$date <- as.Date(ts$date)

# Keep dates where at least half the reservoir was cloud-free
good <- subset(ts, frac_valid >= 0.5)
print(table(good$reservoir))

# Temporal resolution: median days between usable observations
gap <- function(d) median(as.numeric(diff(sort(unique(d)))))
print(tapply(ts$date, ts$reservoir, gap))
print(tapply(good$date, good$reservoir, gap))

# Peaks: top n dates by NDCI p90 per reservoir, at least min_gap days apart
pick_peaks <- function(d, n = 5, min_gap = 30) {
  d <- d[order(-d$ndci_p90), ]
  keep <- d[0, ]
  for (i in seq_len(nrow(d))) {
    if (nrow(keep) == 0 || all(abs(as.numeric(d$date[i] - keep$date)) >= min_gap))
      keep <- rbind(keep, d[i, ])
    if (nrow(keep) == n) break
  }
  keep
}
peaks <- do.call(rbind, lapply(split(good, good$reservoir), pick_peaks))
rownames(peaks) <- NULL
print(peaks[, c("reservoir", "date", "ndci_p50", "ndci_p90", "b4_p50",
                "frac_high_nir", "frac_valid")])
# Images for any date are in the dashboard, or images/<reservoir>/<date>_{rgb,ndci}.webp

# Monthly climatology: is the current value unusual for the season?
good$month <- as.integer(format(good$date, "%m"))
clim <- aggregate(ndci_p90 ~ reservoir + month, good, quantile, probs = c(.25, .5, .75))
print(clim)

yearly <- scale_x_date(date_breaks = "1 year", date_labels = "%Y",
                       expand = expansion(mult = 0.01))
p_ndci <- ggplot(good, aes(date)) +
  geom_line(aes(y = ndci_p50), alpha = 0.4) +
  geom_point(aes(y = ndci_p50), size = 0.8) +
  geom_point(aes(y = ndci_p90), colour = "firebrick", size = 0.8, alpha = 0.6) +
  geom_point(data = peaks, aes(y = ndci_p90), shape = 21, size = 3, stroke = 0.8) +
  facet_wrap(~ reservoir, ncol = 1) + yearly +
  labs(x = NULL, y = "NDCI (black = median, red = p90, ring = peak)") +
  theme_bw() + theme(panel.grid.minor = element_blank())

p_b4 <- ggplot(good, aes(date, b4_p50)) +
  geom_point(size = 0.8, colour = "sienna") +
  facet_wrap(~ reservoir, ncol = 1) + yearly +
  labs(x = NULL, y = "B4 reflectance (median)") +
  theme_bw() + theme(panel.grid.minor = element_blank())

print(p_ndci)
print(p_b4)
