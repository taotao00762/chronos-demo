# Test script for Phase 3.2 imports
import sys
sys.path.insert(0, 'E:/baoke/chronos')

from router import get_route_from_index, get_index_from_route, ROUTES
from components.stat_card import create_stat_card, create_progress_card
from views.dashboard_view import create_dashboard_view

print('ROUTES:', ROUTES)
print('get_route_from_index(2):', get_route_from_index(2))
print('get_index_from_route("/chat"):', get_index_from_route('/chat'))
print('create_stat_card:', create_stat_card)
print('create_dashboard_view:', create_dashboard_view)
print('All Phase 3.2 imports successful!')
