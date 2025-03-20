import pandas as pd
import re

class GoodreadsAnalytics:
    def __init__(self, data_source):
        """
        Initialize the GoodreadsAnalytics class with Goodreads export data.
        
        Parameters:
        data_source (str or pandas.DataFrame): Either a file path to a CSV or a pandas DataFrame
        """
        if isinstance(data_source, str):
            # If a string is provided, assume it's a file path
            self.df = pd.read_csv(data_source, encoding='utf-8')
        elif isinstance(data_source, pd.DataFrame):
            # If a DataFrame is provided, use it directly
            self.df = data_source.copy()
        else:
            raise TypeError("data_source must be either a file path string or a pandas DataFrame")
        
        # Clean up the bookshelves and bookshelves with positions columns
        self._clean_bookshelves()
    
    def _clean_bookshelves(self):
        """Clean and process the bookshelves columns for easier analysis."""
        # Create lists of bookshelves for each book
        if 'Bookshelves' in self.df.columns:
            self.df['bookshelves_list'] = self.df['Bookshelves'].fillna('').apply(
                lambda x: [shelf.strip() for shelf in x.split(',')] if x else []
            )
        
        # Create lists of bookshelves with positions for each book
        if 'Bookshelves with positions' in self.df.columns:
            self.df['bookshelves_positions_list'] = self.df['Bookshelves with positions'].fillna('').apply(
                lambda x: [re.sub(r' \(#\d+\)', '', shelf.strip()) for shelf in x.split(',')] if x else []
            )
    
    def shelf_overlap_percentage(self, shelf1: str, shelf2: str):
        """
        Calculate what percentage of books on shelf1 are also on shelf2.
        
        Parameters:
        shelf1 (str): The primary bookshelf name
        shelf2 (str): The bookshelf to check for overlap
        
        Returns:
        float: Percentage of books from shelf1 that are also on shelf2
        """
        # Get books that are on shelf1
        shelf1_books = self.df[self.df['bookshelves_list'].apply(
            lambda x: any(shelf1.lower() == s.lower() for s in x)
        )]
        
        if len(shelf1_books) == 0:
            return 0.0
        
        # Count how many of these books are also on shelf2
        shelf1_and_shelf2_books = shelf1_books[shelf1_books['bookshelves_list'].apply(
            lambda x: any(shelf2.lower() == s.lower() for s in x)
        )]
        
        # Calculate percentage
        overlap_percentage = (len(shelf1_and_shelf2_books) / len(shelf1_books)) * 100
        
        return overlap_percentage
    
    def average_pages_on_shelf(self, shelf, only_read=False):
        """
        Calculate the average number of pages for books on a given shelf.
        
        Parameters:
        shelf (str): The bookshelf name
        only_read (bool): If True, only consider books that are also on the 'read' shelf
        
        Returns:
        float: Average number of pages
        dict: Additional statistics (min, max, median, total books, total pages)
        """
        # Get books that are on the specified shelf
        shelf_books = self.df[self.df['bookshelves_list'].apply(lambda x: shelf.lower() in [s.lower() for s in x])]
        
        if only_read:
            # Filter to only books that are also on the 'read' shelf
            shelf_books = shelf_books[shelf_books['bookshelves_list'].apply(
                lambda x: 'read' in [s.lower() for s in x]
            )]
        
        if len(shelf_books) == 0:
            return 0.0, {
                'min_pages': 0,
                'max_pages': 0,
                'median_pages': 0,
                'total_books': 0,
                'total_pages': 0
            }
        
        # Convert 'Number of Pages' to numeric, coercing errors to NaN
        pages = pd.to_numeric(shelf_books['Number of Pages'], errors='coerce')
        
        # Remove NaN values
        pages = pages.dropna()
        
        if len(pages) == 0:
            return 0.0, {
                'min_pages': 0,
                'max_pages': 0,
                'median_pages': 0,
                'total_books': len(shelf_books),
                'total_pages': 0
            }
        
        # Calculate average
        avg_pages = pages.mean()
        
        # Additional statistics
        stats = {
            'min_pages': pages.min(),
            'max_pages': pages.max(),
            'median_pages': pages.median(),
            'total_books': len(shelf_books),
            'total_pages': pages.sum()
        }
        
        return avg_pages, stats
    
    def get_shelf_books(self, shelf):
        """
        Get a DataFrame of all books on a specific shelf.
        
        Parameters:
        shelf (str): The bookshelf name
        
        Returns:
        pandas.DataFrame: Books on the specified shelf
        """
        return self.df[self.df['bookshelves_list'].apply(lambda x: shelf.lower() in [s.lower() for s in x])]
    
    def top_rated_books_on_shelf(self, shelf, n=5):
        """
        Get the top N rated books on a specific shelf based on user ratings.
        
        Parameters:
        shelf (str): The bookshelf name
        n (int): Number of top books to return
        
        Returns:
        pandas.DataFrame: Top rated books with title, author, and rating
        """
        shelf_books = self.get_shelf_books(shelf)
        
        # Convert 'My Rating' to numeric
        shelf_books['My Rating'] = pd.to_numeric(shelf_books['My Rating'], errors='coerce')
        
        # Sort by rating (descending)
        top_books = shelf_books.sort_values(by='My Rating', ascending=False).head(n)
        
        # Select relevant columns
        if not top_books.empty:
            return top_books[['Title', 'Author', 'My Rating']]
        else:
            return pd.DataFrame(columns=['Title', 'Author', 'My Rating'])
    
    def reading_stats(self):
        """
        Generate overall reading statistics from the Goodreads data.
        
        Returns:
        dict: Various reading statistics
        """
        # Books read
        read_books = self.df[self.df['bookshelves_list'].apply(lambda x: 'read' in [s.lower() for s in x])]
        
        # Books to read
        to_read_books = self.df[self.df['bookshelves_list'].apply(lambda x: 'to-read' in [s.lower() for s in x])]
        
        # Calculate average rating given
        my_ratings = pd.to_numeric(read_books['My Rating'], errors='coerce')
        avg_rating = my_ratings[my_ratings > 0].mean()
        
        # Get distribution of ratings
        rating_dist = my_ratings[my_ratings > 0].value_counts().sort_index().to_dict()
        
        # Stats dict
        stats = {
            'total_books': len(self.df),
            'books_read': len(read_books),
            'books_to_read': len(to_read_books),
            'avg_rating': avg_rating,
            'rating_distribution': rating_dist,
            'percent_read': (len(read_books) / len(self.df)) * 100 if len(self.df) > 0 else 0
        }
        
        return stats


# Example usage
if __name__ == "__main__":
    # Create an instance of the class with the CSV file
    analytics = GoodreadsAnalytics("/Users/griffinansel/Desktop/Projects/goodreads_utils/goodreads-analytics/griffin_goodreads.csv")
    
    # Example 1: Calculate what percentage of books on 'nyc-collection' are also on 'read'
    nyc_read_overlap = analytics.shelf_overlap_percentage(shelf1="nyc-collection", shelf2="read")
    print(f"Percentage of NYC Collection books that have been read: {nyc_read_overlap:.2f}%")
    
    # Example 2: Calculate average pages for all books on 'nyc-collection'
    avg_pages, page_stats = analytics.average_pages_on_shelf("nyc-collection")
    print(f"Average pages in NYC Collection: {avg_pages:.1f}")
    print(f"Page stats: {page_stats}")
    
    # Example 3: Calculate average pages for read books on 'nyc-collection'
    avg_pages_read, page_stats_read = analytics.average_pages_on_shelf("nyc-collection", only_read=True)
    print(f"Average pages in read NYC Collection books: {avg_pages_read:.1f}")
    print(f"Page stats for read books: {page_stats_read}")