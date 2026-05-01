import sys
sys.path.insert(0, '.')
try:
    from freeze_guard import get_procurement_recommendation
except ImportError:
    from core.freeze_guard import get_procurement_recommendation

clusters = {0: ['F01','F02','F03'], 1: ['F04','F05']}
unstable_ids = ['F04']

# Zone 1: SAFE (DI=8)
r1 = get_procurement_recommendation(8, clusters, unstable_ids)
print('SAFE:', r1['action'])
assert 'PROCURE ALL' in r1['action'], f"Got: {r1['action']}"

# Zone 2: WARNING (DI=12)
r2 = get_procurement_recommendation(12, clusters, unstable_ids)
print('WARNING:', r2['action'])
assert 'STABLE' in r2['action'], f"Got: {r2['action']}"
assert 0 in r2['stable_clusters'], f"Cluster 0 should be stable"
assert 1 in r2['unstable_clusters'], f"Cluster 1 should be unstable"

# Zone 3: HALT (DI=20)
r3 = get_procurement_recommendation(20, clusters, unstable_ids)
print('HALT:', r3['action'])
assert 'HALT' in r3['action'], f"Got: {r3['action']}"

print('All 3 zones pass')
