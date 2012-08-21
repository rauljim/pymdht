# Release checklist:

cd ~/git/pymdht/release_tools/
git checkout develop

# If you have more up-to-date nodes in local.
# A pymdht.bootstrap from node running 24/7 is best.
cp ~/.pymdht/pymdht.bootstrap ../core/bootstrap_unstable

# Run the crawler to update bootstrap nodes (it takes around 4 days)
rm crawled24.nodes.release-*
./crawl24.py 

# Replace bootstrap_unstable with the list created by crawler
sort crawled.nodes.release-* >../core/bootstrap_unstable

# Commit core/bootstrap_unstable
git commit ../core/bootstrap_unstable -m 'bootstrap nodes updated'

# Upgrade version in: CHANGES.txt README.rst setup.py core/pymdht.py
# From develop (odd) to stable (even)
# Example:
# https://github.com/rauljim/pymdht/commit/e8535488923fe6b4abe0438d8295c818f3bf1306

# Commit
git commit CHANGES.txt README.rst setup.py core/pymdht.py -m \
'version upgrade xx.x.odd > xx.x.even'
git push origin release/xx.x.even

# Create release branch. Feature freeze. No development in this branch!!!
# Just debugging.
git checkout -b release/xx.x.even

# Back to develop
git checkout develop

# Upgrade version in: CHANGES.txt README.rst setup.py core/pymdht.py
# From stable (even) to develop (odd)
# Example:
# https://github.com/rauljim/pymdht/commit/baa1a3da0177364692d99bfc192e82e1380b0381

# Commit
git commit CHANGES.txt README.rst setup.py core/pymdht.py -m \
'version upgrade xx.x.x > xx.x.even+1'

# If you find a bug, fix it in the release branch. Then, merge it into develop.
# Never the other way around.



