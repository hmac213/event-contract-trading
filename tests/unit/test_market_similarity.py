import unittest
from unittest.mock import MagicMock, patch
from services.market_similarity.main import MarketSimilarityService, Market, PlatformType

class TestMarketSimilarityService(unittest.TestCase):

    @patch('services.market_similarity.main.RedisManager')
    @patch('services.market_similarity.main.DBManager')
    @patch('services.market_similarity.main.SimilarityDBManager')
    @patch('services.market_similarity.main.OpenAI')
    @patch('services.market_similarity.main.instructor.patch')
    def test_process_market_events_with_similar_markets(self, mock_instructor_patch, mock_openai, mock_similarity_db_manager, mock_db_manager, mock_redis_manager):
        # Arrange
        mock_redis = mock_redis_manager.return_value
        mock_db = mock_db_manager.return_value
        mock_sim_db = mock_similarity_db_manager.return_value
        mock_openai_client = MagicMock()
        mock_instructor_patch.return_value = mock_openai_client
        
        message_id = '12345-0'
        market_data = {
            'market_id': 'MARKET_1', 'platform': PlatformType.KALSHI.value,
            'name': 'Market 1 Name', 'rules': 'Market 1 Rules',
            'close_timestamp': 123456789
        }
        mock_redis.read_from_stream.return_value = [(message_id, market_data)]

        candidate_market = Market(
            market_id='MARKET_2', platform=PlatformType.POLYMARKET,
            name='Market 2 Name', rules='Market 2 Rules',
            close_timestamp=123456789
        )
        mock_sim_db.find_similar_markets.return_value = ['MARKET_2']
        mock_db.get_markets.return_value = [candidate_market]
        
        # Mock GPT to return True for similarity
        mock_prediction = MagicMock()
        mock_prediction.final_answer = True
        mock_openai_client.chat.completions.create.return_value = mock_prediction

        # Act
        service = MarketSimilarityService()
        service.process_market_events()

        # Assert
        mock_redis.add_to_stream.assert_called_once()
        mock_db.add_market_pairs.assert_called_once()
        mock_redis.acknowledge_message.assert_called_with(service.input_stream_name, service.group_name, message_id)

    @patch('services.market_similarity.main.RedisManager')
    @patch('services.market_similarity.main.DBManager')
    @patch('services.market_similarity.main.SimilarityDBManager')
    @patch('services.market_similarity.main.OpenAI')
    @patch('services.market_similarity.main.instructor.patch')
    def test_process_market_events_no_similar_markets(self, mock_instructor_patch, mock_openai, mock_similarity_db_manager, mock_db_manager, mock_redis_manager):
        # Arrange
        mock_redis = mock_redis_manager.return_value
        mock_db = mock_db_manager.return_value
        mock_sim_db = mock_similarity_db_manager.return_value
        
        message_id = '12345-0'
        market_data = {
            'market_id': 'MARKET_1', 'platform': PlatformType.KALSHI.value,
            'name': 'Market 1 Name', 'rules': 'Market 1 Rules',
            'close_timestamp': 123456789
        }
        mock_redis.read_from_stream.return_value = [(message_id, market_data)]
        mock_sim_db.find_similar_markets.return_value = [] # No candidates

        # Act
        service = MarketSimilarityService()
        service.process_market_events()

        # Assert
        mock_redis.add_to_stream.assert_not_called()
        mock_db.add_market_pairs.assert_not_called()
        mock_redis.acknowledge_message.assert_called_with(service.input_stream_name, service.group_name, message_id)

    @patch('services.market_similarity.main.RedisManager')
    @patch('services.market_similarity.main.DBManager')
    @patch('services.market_similarity.main.SimilarityDBManager')
    @patch('services.market_similarity.main.OpenAI')
    @patch('services.market_similarity.main.instructor.patch')
    def test_process_market_events_dissimilar_markets(self, mock_instructor_patch, mock_openai, mock_similarity_db_manager, mock_db_manager, mock_redis_manager):
        # Arrange
        mock_redis = mock_redis_manager.return_value
        mock_db = mock_db_manager.return_value
        mock_sim_db = mock_similarity_db_manager.return_value
        mock_openai_client = MagicMock()
        mock_instructor_patch.return_value = mock_openai_client

        message_id = '12345-0'
        market_data = {
            'market_id': 'MARKET_1', 'platform': PlatformType.KALSHI.value,
            'name': 'Market 1 Name', 'rules': 'Market 1 Rules',
            'close_timestamp': 123456789
        }
        mock_redis.read_from_stream.return_value = [(message_id, market_data)]
        
        candidate_market = Market(
            market_id='MARKET_2', platform=PlatformType.POLYMARKET,
            name='Market 2 Name', rules='Market 2 Rules',
            close_timestamp=123456789
        )
        mock_sim_db.find_similar_markets.return_value = ['MARKET_2']
        mock_db.get_markets.return_value = [candidate_market]
        
        # Mock GPT to return False
        mock_prediction = MagicMock()
        mock_prediction.final_answer = False
        mock_openai_client.chat.completions.create.return_value = mock_prediction

        # Act
        service = MarketSimilarityService()
        service.process_market_events()

        # Assert
        mock_redis.add_to_stream.assert_not_called()
        mock_db.add_market_pairs.assert_not_called()
        mock_redis.acknowledge_message.assert_called_with(service.input_stream_name, service.group_name, message_id)

if __name__ == '__main__':
    unittest.main() 