import ecg
from ecg import jgi
domain="*Microbiome"
path = "myjgi"
J = jgi.Jgi()
J.scrape_domain(path, domain)