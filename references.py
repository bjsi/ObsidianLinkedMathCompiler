class References:

    Author: str = ""
    Title: str = ""
    Source: str = ""
    Link: str = ""
    Email: str = ""
    Comment: str = ""

    def to_dict(self):
        return {
            "Author": self.Author,
            "Title": self.Title,
            "Source": self.Source,
            "Link": self.Link,
            "Email": self.Email,
            "Comment": self.Comment,
        }

